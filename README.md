# GCP Healthcare Foundation (Terraform reference)

A lean, multi-environment GCP **landing zone + healthcare data platform**,
structured as sequential TEF-style stages. It builds the compliant foundation
(org, policies, audit, networking, projects, VPC-SC) and the healthcare
workload (Cloud Healthcare API, BigQuery medallion lakehouse, DLP, CLS/RLS)
from the two reference architecture diagrams.

> **Reference codebase, greenfield.** Values are placeholders; nothing is wired
> to a live org. It is organized like a real deployment and meant to be
> `terraform validate`/`plan`-ed in your own environment after you fill in
> `org_id`, `billing_account`, groups, and IP ranges. It was **not** validated
> against live GCP APIs here.

## Architecture Roadmap

The target architecture is captured in the
[`docs/architecture/ROADMAP.md`](docs/architecture/ROADMAP.md) roadmap:

- **End-to-end, seven compliance pillars** — `docs/architecture/01-end-to-end-seven-pillars.png`
- **HIPAA-compliant data architecture** — `docs/architecture/02-hipaa-compliant-architecture.png`

## Stages (apply in order)

| Stage | Builds |
|---|---|
| `0-bootstrap` | Seed project, CMEK state bucket, foundation Terraform SA |
| `1-org` | Folder hierarchy, org policies, immutable audit logging, SCC, contacts |
| `2-environments` | Per-env base project, CMEK key, billing budget |
| `3-networks` | Per-env Shared VPC, firewall/egress lockdown, NAT, DNS, VPC-SC perimeters |
| `4-projects` | Workload projects (ingestion/healthcare-core/lakehouse/delivery), perimeter membership |
| `5-healthcare-workload` | Healthcare API stores, BQ medallion lakehouse, DLP, CLS/RLS, workload IAM |
| `6-monitoring` | Org-wide security alerting (IAM/VPC-SC/KMS), per-env metrics scope + dashboards |

Shared logic lives in `modules/` (`env-baseline`, `net-env`, `workload-project`,
`hybrid-vpn`, `monitoring-env`). CI/CD is in `.github/workflows/terraform.yml`
(keyless via Workload Identity Federation). Hybrid connectivity (HA VPN to
on-prem) is optional in `3-networks` via `var.vpn_config`.

## How state flows
`0-bootstrap` creates the GCS state bucket, then every later stage stores its
state there under a distinct `prefix` and reads upstream stages via
`terraform_remote_state`. Org-wide settings (org_id, billing, prefix, region)
have a single source of truth in bootstrap outputs.

## Quick start
```bash
# 1. Bootstrap (run as a human/org admin; starts on local state)
cd 0-bootstrap
cp terraform.tfvars.example terraform.tfvars   # fill real values
gcloud auth application-default login
terraform init && terraform apply
# then uncomment backend.tf with the printed bucket and: terraform init -migrate-state

# 2..5: set bootstrap_state_bucket + backend bucket in each, then in order:
for s in 1-org 2-environments 3-networks 4-projects 5-healthcare-workload 6-monitoring; do
  ( cd $s && terraform init && terraform apply )
done
```

## Conventions
- Project IDs: `<prefix>-<envshort>-<component>` (e.g. `hcf-prod-lakehouse`).
- Operators authenticate as themselves and **impersonate** the foundation SA;
  no service-account keys exist anywhere.
- Everything at rest is CMEK-encrypted with per-environment keys.

## Key caveats
See each stage README and `docs/COMPLIANCE.md`. Most notable: Healthcare API
CMEK is set outside Terraform (provider gap); the egress deny-all is strict by
design; one org-scoped VPC-SC access policy per org (import if one exists).
