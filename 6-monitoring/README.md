# 6-monitoring

Monitoring, alerting, and security detection across the platform.

## What it creates
**Org-wide security alerting** (in the logging project):
- An aggregated org sink routing all audit logs into the logging project so
  log-based metrics see every project.
- Log-based metrics + alert policies for: IAM policy changes, **VPC-SC
  violations**, service-account key creation, and KMS key destruction.
- An email notification channel.

**Per-environment operational monitoring** (`modules/monitoring-env`):
- Each env base project becomes a **metrics scope** observing all that env's
  workload projects (ingestion/healthcare-core/lakehouse/delivery).
- An ops email notification channel + a starter dashboard.

## Run
1. Set `bootstrap_state_bucket`, the `backend.tf` bucket, and `alert_email`.
2. `terraform init && terraform apply`

## Notes
- Security alerting works by routing child audit logs into the logging
  project's `_Default` bucket; log-based metrics there then match org-wide.
  This complements (does not replace) the immutable GCS audit archive from
  stage 1, which is for retention, not alerting.
- Extend `modules/monitoring-env` dashboards with Healthcare API / Dataflow /
  BigQuery widgets as those workloads deploy.
- Wire the notification channel to PagerDuty/Slack by adding channels of those
  types and referencing them in the alert policies.
