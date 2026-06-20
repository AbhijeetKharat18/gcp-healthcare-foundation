# 1-org

Organization-level configuration: hierarchy, guardrails, audit, and security
notifications. Runs as the foundation SA (impersonation) on remote state.

## What it creates
- **Folder hierarchy:** `fldr-common` + one folder per environment
  (`development`, `nonproduction`, `production`).
- **Org policies (compliance by design):** no SA keys, no default network,
  OS Login required, no public Cloud SQL IPs, uniform bucket access, no serial
  port, **deny VM external IPs**, **resource-location restriction** (data
  residency), and **CMEK required** for BigQuery / Storage / Healthcare / Pub/Sub.
- **Central logging:** dedicated logging project, an **immutable
  (bucket-locked), CMEK-encrypted** audit archive, and an **org-level
  aggregated sink** capturing Cloud Audit logs from every project.
- **Security:** SCC active-findings export to Pub/Sub (SIEM-ready) and
  Essential Contacts for security/technical/suspension notices.

## Design notes
- CMEK org policy and the CMEK'd log bucket are intentionally consistent: the
  bucket must be encrypted with a key, or it would violate our own policy.
- Audit retention defaults to ~7 years and is **locked** — it cannot be
  shortened, only the bucket destroyed after retention. Tune `audit_log_retention_days`.
- `allowed_locations` defaults to US only; change for your residency needs.

## Run
1. Set `bootstrap_state_bucket` and `backend.tf` bucket to the 0-bootstrap output.
2. `terraform init && terraform apply`

## Outputs (downstream)
`common_folder_id`, `environment_folder_ids`, `logging_project_id`,
`audit_archive_bucket`, `scc_findings_topic`.

## Compliance mapping (high level)
| Control | Resource |
|---|---|
| Audit controls / immutable retention | `google_storage_bucket.audit_logs` (bucket lock) + org sink |
| Data residency | `gcp.resourceLocations` org policy |
| Encryption at rest (CMEK) | `gcp.restrictNonCmekServices` org policy |
| Threat detection / response | SCC notification config -> Pub/Sub |
| Least privilege baseline | SA-key + OS Login + external-IP policies |

> Full requirement-by-requirement mapping lives in `../docs/COMPLIANCE.md`
> (added with stage 5).
