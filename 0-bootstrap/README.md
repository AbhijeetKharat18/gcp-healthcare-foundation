# 0-bootstrap

Bootstraps a greenfield GCP organization for the healthcare foundation.

## What it creates
- **Seed project** (`hcf-b-seed`) under the org — holds state + the Terraform SA.
- **CMEK-encrypted state bucket** (versioned, uniform access, public access blocked).
- **`sa-terraform-foundation`** service account — the identity every later stage runs as, with the org-level roles needed to build folders, projects, policies, networking, and VPC-SC.
- **Break-glass IAM** for the org-admin and billing-admin groups, plus impersonation rights so operators run Terraform *as* the SA.

## Why one seed project (lean / option A)
TEF splits seed and CI/CD into two projects for separation of duties. Here we keep a single seed project for readability. The split is noted in `main.tf` as the production hardening step.

## How to run (greenfield)
1. `cp terraform.tfvars.example terraform.tfvars` and fill `org_id`, `billing_account`, groups.
2. Authenticate as a user who can create projects under the org:
   `gcloud auth application-default login`
3. `terraform init && terraform apply`  (starts on **local** state)
4. Uncomment `backend.tf` with the printed `tfstate_bucket`, then
   `terraform init -migrate-state` to move state into the bucket.

## Outputs (consumed downstream)
`seed_project_id`, `tfstate_bucket`, `terraform_sa_email`, `tfstate_kms_key`,
and pass-throughs `org_id`, `billing_account`, `project_prefix`, `default_region`.

> Reference codebase: variables are placeholders and nothing is wired to a live
> org. Run `terraform validate` / `plan` in your own environment.
