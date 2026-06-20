# ---------------------------------------------------------------------------
# 0-bootstrap / outputs.tf
# Later stages read these via terraform_remote_state (see 1-org/main.tf).
# We also pass through org-wide settings so downstream stages have one source
# of truth instead of re-declaring org_id / billing in every stage.
# ---------------------------------------------------------------------------

output "seed_project_id" {
  description = "Seed project holding state + Terraform SA."
  value       = google_project.seed.project_id
}

output "tfstate_bucket" {
  description = "GCS bucket name for Terraform remote state."
  value       = google_storage_bucket.tfstate.name
}

output "terraform_sa_email" {
  description = "Service account later stages impersonate."
  value       = google_service_account.terraform.email
}

output "tfstate_kms_key" {
  description = "CMEK key protecting state."
  value       = google_kms_crypto_key.tfstate.id
}

# --- Pass-through org settings ----------------------------------------------
output "org_id" {
  value = var.org_id
}

output "billing_account" {
  value = var.billing_account
}

output "project_prefix" {
  value = var.project_prefix
}

output "default_region" {
  value = var.default_region
}

# --- CI/CD (Workload Identity Federation) -----------------------------------
output "wif_provider_name" {
  description = "Full WIF provider resource name for google-github-actions/auth."
  value       = google_iam_workload_identity_pool_provider.github.name
}
