# QA Report — NL Analytics Assistant (POC #1)

Pre-GCP quality assurance: everything that can be verified **without a GCP
subscription** has been. This documents what was tested, the results, and what
is necessarily deferred until a GCP project exists.

_Last run: 2026-09-20. Environment: Python 3.11, Linux (Apple-Silicon macOS is
equivalent — all deps ship arm64 wheels)._

## Summary

| Gate | Result |
|---|---|
| Unit / integration tests | **106 passing**, 0 failing |
| Coverage (`nl_analytics`) | **98%** |
| Static analysis (ruff) | **clean** |
| Browser E2E (Playwright/Chromium) | **2 passing** |
| Terraform `fmt` | **clean** (validate runs in CI where the registry is reachable) |
| Synthetic data | referential integrity + de-identification enforced by tests; generation is deterministic |
| Live local-model test (Ollama) | opt-in, runs on the machine with Ollama |

Run it all offline with: `make qa` (lint + coverage) and `make qa-e2e` (browser).

## What was tested

### 1. Guardrails — the security-critical layer
Verified by unit tests and adversarial fuzzing. Every generated query must pass
`guardrails.enforce()` before execution.

| Attack / case | Result |
|---|---|
| `DELETE` / `UPDATE` / `INSERT` / `TRUNCATE` / `MERGE` | blocked |
| `DROP` / `CREATE TABLE` / `CREATE VIEW` / `ALTER` | blocked |
| `GRANT`, `CALL <proc>` | blocked |
| `EXPORT DATA ... AS SELECT` (GCS exfiltration) | blocked |
| Read of `raw_phi` / `standardized_phi` / `curated_phi` | blocked |
| Out-of-scope dataset hidden in a **CTE** | blocked |
| Out-of-scope dataset hidden in a **subquery** | blocked |
| Stacked statement after `--` or `/* */` comment | blocked |
| Wrong-dataset qualifier on an allowed table name | blocked |
| Unqualified allowed table | allowed, normalised to `secure_views.<t>` |
| `LIMIT` absent / oversized / non-integer | injected / capped / overridden |

The read-only gate is a **positive allowlist of query root types** (fails
closed), so unknown/new statement types are rejected by default.

### 2. End-to-end pipeline
`question → LLM → guardrails → dry-run → execute → answer`, tested with the mock
provider + DuckDB over synthetic data: all sample questions return correct
aggregates; error paths at every stage (generate / guardrail / dry_run /
execute) return clean, staged errors rather than crashing.

### 3. Providers (all four)
- **mock** — canned SQL, exercises the pipeline deterministically.
- **vertex** (Gemini/Vertex) — logic tested with a stubbed SDK: prompt assembly,
  blocked/empty response handling, `clean_sql`.
- **aistudio** (Gemini/free key) — same, with a faked client.
- **ollama** (local) — request shape, prose/fence extraction, connection-failure
  handling, faked client; plus an opt-in live test against real Ollama.

### 4. Executors
- **duckdb** — real execution over synthetic data, BigQuery→DuckDB transpilation
  (`COUNTIF`, `SAFE_DIVIDE`), qualified/unqualified resolution, type coercion
  (DATE→ISO, NUMERIC→float), missing-data error.
- **bigquery** — dry-run, execute, row/type conversion, cost cap, tested with a
  faked client (no cloud).

### 5. HTTP API + UI
- All endpoints (`/healthz`, `/`, `/api/schema`, `/api/samples`, `/api/prompt`,
  `/api/ask`) tested; input validation (oversized/empty/missing) returns 422.
- **Real browser E2E** (headless Chromium): loads the page, asks a question,
  asserts SQL + results render; submits an out-of-scope query, asserts the
  guardrail message appears.

### 6. Synthetic data integrity
Referential integrity across all five tables, valid domains (age bands,
non-negative LOS, readmission only for inpatient), and — enforced by test — **no
direct-identifier columns** (no name/MRN/SSN/DOB/phone/email/address). Data
generation is deterministic (byte-identical on regeneration).

### 7. Static analysis & CI
`ruff` clean across app + data. CI (`.github/workflows/poc-nl-analytics.yml`)
runs lint, tests+coverage, browser E2E, a Docker image build, and Terraform
fmt/validate — scoped to the POC path so it never touches the foundation
pipeline.

## Deferred until a GCP project exists

These require live GCP and are **not** testable pre-subscription:

- Real Gemini-on-Vertex generation (validated locally via AI Studio / Ollama instead).
- Querying the real `secure_views` in BigQuery (validated locally via DuckDB on synthetic data).
- Cloud Run deployment, VPC-SC perimeter behaviour, and `sa-delivery` IAM in a live org.
- `terraform plan/apply` against the real org (fmt/validate pass offline).

## How to reproduce

```bash
cd poc/nl-analytics-assistant
make setup
make qa                 # ruff + tests + coverage (fully offline)
make qa-e2e             # browser E2E (run `.venv/bin/playwright install chromium` once)
make demo-ollama        # real local model, fully offline  (or make demo-gemini)
make qa-live-ollama     # optional: live model integration test
```

## Sign-off checklist

- [x] All offline tests green (106)
- [x] Coverage ≥ 95% (98%)
- [x] Lint clean
- [x] Guardrail attack matrix passes
- [x] Browser E2E passes
- [x] Data integrity + de-identification enforced
- [x] Terraform fmt clean
- [ ] Post-GCP: Vertex + BigQuery live smoke test (after subscription)
- [ ] Post-GCP: Cloud Run deploy + VPC-SC validation (after subscription)
