# ---------------------------------------------------------------------------
# 0-bootstrap / versions.tf
# Provider + Terraform version constraints for the whole foundation.
# Pin these to known-good versions (TEF pins; we follow the same practice).
# ---------------------------------------------------------------------------

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.40.0, < 6.0.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = ">= 5.40.0, < 6.0.0"
    }
  }
}

# NOTE (greenfield):
# Bootstrap is the ONLY stage that starts with local state, because the
# remote state bucket does not exist yet. After the first apply creates the
# bucket (see state.tf), uncomment backend.tf and run `terraform init -migrate-state`.
