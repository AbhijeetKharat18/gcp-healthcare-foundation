# NL Analytics Assistant (POC #1)

**Ask the healthcare lakehouse questions in plain English — safely.**

This is the first AI application built on the `gcp-healthcare-foundation`
landing zone. It turns natural-language questions ("what's the 30-day
readmission rate by facility?") into governed BigQuery SQL, runs it against the
**`secure_views`** layer only, and returns the answer *plus the exact SQL it
ran*.

It is designed to showcase the thing that makes this platform special: you can
put a modern LLM in front of clinical data **and prove it stays inside the
guardrails** — de-identified data only, read-only, `secure_views` only,
in-perimeter, fully auditable.

> Value: High · Effort: Low · Differentiation: High

---

## Why this is a good fit for the foundation

| It uses… | …which already exists in the foundation |
|---|---|
| `secure_views` (governed, de-identified) | `5-healthcare-workload/secure-views.tf`, `lakehouse.tf` |
| `sa-delivery` (reads secure_views only) | `5-healthcare-workload/iam.tf` |
| Vertex AI + Cloud Run + BigQuery APIs | enabled on the `delivery` project (`4-projects/variables.tf`) |
| VPC-SC perimeter + CMEK + audit sink | stages 1 / 3 / 6 |

The POC adds only what was missing: the application runtime, and two IAM grants
(`aiplatform.user`, `bigquery.jobUser`) so `sa-delivery` can call Gemini and run
query jobs. It gains **no new data-read scope**.

## How it works

```
question
  → Gemini on Vertex AI      (grounded ONLY on the secure_views catalog)
  → guardrails.enforce()     ← trust gate: SELECT-only · allowlist · LIMIT
  → dry-run                  (validity / cost check, capped bytes)
  → execute                  (reads secure_views only, as sa-delivery)
  → answer + the exact SQL   (transparency)
```

The **guardrails** (`app/nl_analytics/guardrails.py`) are the heart of it. Even
if a prompt-injection convinced the model to emit something dangerous, it never
runs. Using `sqlglot`, every generated query must:

1. parse as exactly one statement (no stacked queries);
2. be read-only (any INSERT/UPDATE/DELETE/MERGE/DDL/command is rejected);
3. reference only allow-listed `secure_views` tables — never `raw_phi`,
   `standardized_phi`, or `curated_phi`;
4. carry a row `LIMIT` no larger than the configured cap (injected/capped).

This is defence-in-depth *on top of* the IAM boundary — belt and braces.

## Architecture: swappable by design

- **LLM provider** (`app/nl_analytics/llm/`): `vertex` (Gemini, production),
  `aistudio` (Gemini via a free AI Studio key), `ollama` (a local model, fully
  offline), or `mock` (deterministic, offline). Swapping to Claude-on-Vertex
  later is a new provider class, not a rewrite.
- **Executor** (`app/nl_analytics/executor/`): `bigquery` (production) or
  `duckdb` (local synthetic data). The local path transpiles the *real*
  BigQuery SQL to DuckDB, so the demo exercises the same guardrail path as prod.

## Run the demo locally (no GCP needed)

```bash
cd poc/nl-analytics-assistant
make setup     # venv + dev deps
make data      # (already committed, but regenerates the synthetic data)
make demo      # http://localhost:8080   (mock LLM + DuckDB)
```

Open http://localhost:8080 and try the sample questions, or click
**"See the guardrails in action"** to watch an out-of-scope / destructive
request get blocked before it runs.

Run the tests / full QA gate:

```bash
make test      # unit + integration tests (guardrails, pipeline, API, providers, data)
make qa        # ruff lint + tests with coverage (the offline QA gate)
make qa-e2e    # real browser end-to-end (Playwright/Chromium)
```

See [`docs/QA_REPORT.md`](docs/QA_REPORT.md) for the full pre-GCP QA results
(106 offline tests, 98% coverage, guardrail attack matrix, browser E2E) and what
is deferred until a GCP project exists.

### Test the *real* NL→SQL locally — no GCP

The `mock` provider returns canned SQL, so it exercises the plumbing and
guardrails but not the model's actual generation. Two ways to drive real
natural-language → SQL locally **without a GCP subscription**:

**Fully offline with Ollama** (no key, no internet):

```bash
ollama pull qwen2.5-coder            # a code/SQL-tuned model works best
export NLA_OLLAMA_MODEL=qwen2.5-coder # default is llama3.1
make demo-ollama                     # NLA_PROVIDER=ollama + DuckDB
```

**Free Gemini via Google AI Studio** (closest to production; a free
[API key](https://aistudio.google.com/apikey), no project or billing):

```bash
export NLA_GEMINI_API_KEY=<your-free-key>
make demo-gemini                     # NLA_PROVIDER=aistudio + DuckDB
```

Either way, questions go to a real model, the returned SQL passes the same
guardrails, and results come from the local synthetic data. The only things
that still need GCP are querying the *real* `secure_views` in BigQuery and
deploying to Cloud Run.

**Provider matrix**

| `NLA_PROVIDER` | Model | Needs | Use for |
|---|---|---|---|
| `mock` | canned SQL | nothing | plumbing + guardrail tests |
| `ollama` | local model | Ollama running | real NL→SQL, fully offline |
| `aistudio` | Gemini (AI Studio) | free API key | real NL→SQL, closest to prod |
| `vertex` | Gemini (Vertex) | GCP project | production |

> Running the app **in Docker** against Ollama on the host? Point it at
> `NLA_OLLAMA_HOST=http://host.docker.internal:11434`.

## Deploy to GCP (production path)

Build/push the container, then apply the Terraform. See
[`terraform/README.md`](terraform/README.md). In short:

```bash
docker build -t $IMAGE . && docker push $IMAGE
cd terraform
cp backend.tf.example backend.tf && cp terraform.tfvars.example terraform.tfvars
terraform init && terraform apply
```

The service deploys to the delivery project as `sa-delivery`, with
**internal-only ingress** (front it with an internal LB / IAP for users), so
Vertex and BigQuery traffic never leaves the VPC-SC perimeter.

## Data

`data/` contains a governed `secure_views` schema and a dependency-free
"Synthea-lite" generator producing **de-identified** synthetic rows (age bands
not DOB, zip3 not ZIP+4, tokenised keys not MRNs). No real PHI, ever. The
committed CSVs let the demo run instantly.

## Compliance story (what to show an auditor)

- **Minimum necessary / least privilege**: reads only `secure_views`; the
  runtime identity physically cannot see raw or curated PHI.
- **De-identification**: the exposed columns are already de-identified; the
  catalog test (`test_no_direct_identifier_columns`) enforces it.
- **Read-only + scope enforcement**: guardrails block anything else, verified by
  tests.
- **In-perimeter**: internal-only ingress; VPC-SC governs every Vertex + BigQuery
  call by `sa-delivery`'s identity + perimeter membership (add Direct VPC egress
  for a fully private network path — see `terraform/README.md`).
- **Auditability**: every query runs as `sa-delivery` through BigQuery, captured
  by the foundation's audit sink; the exact SQL is returned to the user.

## Limitations / next steps

- Text-to-SQL can still produce a *logically* wrong-but-safe query; the returned
  SQL keeps a human in the loop. Add result caching and a feedback loop next.
- Row-level security (`SESSION_USER()` views) applies when real curated tables
  exist; wire per-user identity from IAP to demonstrate two users, same
  question, different rows.
- Swap the demo synthetic data for real `secure_views` once curated tables land.
