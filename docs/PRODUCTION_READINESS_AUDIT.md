# Production Readiness Audit Notes

This is a concise audit trail for the production-readiness hardening applied
after the first successful repository push.

## Completed Hardening

- Included `0-bootstrap` in GitHub Actions Terraform validation.
- Formatted `0-bootstrap` with Terraform 1.9.5.
- Enabled `prevent_destroy` on the Terraform state KMS key.
- Started tracking `.terraform.lock.hcl` files so provider selections are
  reproducible across local and CI runs.
- Kept plan/apply guarded until GCP Workload Identity Federation variables are
  configured in GitHub Actions.

## Verified

- Main Terraform stages previously validated successfully with Terraform 1.9.5.
- GitHub Actions validation is green for the current repo workflow.
- Real secrets, `.tfvars`, state files, plans, and service-account key files are
  ignored.

## Remaining Production Decisions

- Replace placeholder org, billing, group, CIDR, and contact values.
- Apply `0-bootstrap` in the target GCP organization.
- Configure GitHub Actions variables from bootstrap outputs:
  `TF_STATE_BUCKET`, `GCP_SERVICE_ACCOUNT`, and `GCP_WIF_PROVIDER`.
- Validate Healthcare API CMEK in the target environment, since that is
  documented as an out-of-band step.
- Decide whether to split the powerful foundation Terraform service account
  into narrower per-stage service accounts or custom roles.
- Test VPC Service Controls with real users, service accounts, perimeter
  bridges, and approved data paths before production go-live.
- Add application runtime deployments for ingestion, harmonization, delivery,
  analytics, and ML workloads.

## Production Gate

Treat this repository as production-style infrastructure code, but do not call
the platform production-ready until live `terraform plan` runs complete against
the target organization and security/compliance owners approve the controls.
