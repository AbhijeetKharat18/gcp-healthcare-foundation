# 2-environments

Per-environment baseline for `development`, `nonproduction`, and `production`.
Driven by a reusable local module (`modules/env-baseline`) so each env is
identical except for name, folder, and budget.

## What it creates (per environment)
- A small **base project** (`hcf-<env>-base`) inside that env's folder.
- An **environment CMEK keyring + key** (90-day rotation) that stages 3–5 use
  to encrypt that environment's data (BigQuery, GCS, Healthcare API, Pub/Sub).
- A **billing budget** scoped by the `environment` label, with alert thresholds
  at 50/75/90/100%.

## Why a per-env base project + key
Centralizing each environment's CMEK in one base project gives a clean blast
radius and a single place to manage key IAM and rotation, instead of scattering
keys across every workload project. Workload projects (stage 4) reference the
env key by ID.

## Run
1. Set `bootstrap_state_bucket` and the `backend.tf` bucket.
2. `terraform init && terraform apply`

## Outputs (downstream)
`environments` — map keyed by short code (`dev`/`nonprod`/`prod`) →
`{ base_project_id, kms_key_id, kms_keyring_id }`.

## Notes
- `providers.tf` sets `user_project_override` + `billing_project` so the global
  Billing Budgets API has a quota project while running as the impersonated SA.
- Budgets filter by the `environment` label; stage-4 projects carry that label,
  so budget scoping "just works" once projects exist.
- Short codes keep project IDs within length limits (`development` → `dev`).
