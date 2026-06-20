# ---------------------------------------------------------------------------
# 0-bootstrap / main.tf
# Creates the "seed" project. This single project holds the Terraform state
# bucket and the Terraform service account that every later stage runs as.
#
# Lean choice (option A): one seed project instead of TEF's separate
# seed + cicd projects. In production you would split these for stronger
# separation of duties.
# ---------------------------------------------------------------------------

locals {
  seed_project_id = "${var.project_prefix}-b-seed" # b = bootstrap

  # APIs the seed project itself needs (state, IAM, KMS for state CMEK, billing).
  seed_apis = [
    "cloudresourcemanager.googleapis.com",
    "cloudbilling.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "serviceusage.googleapis.com",
    "storage.googleapis.com",
    "cloudkms.googleapis.com",
    "orgpolicy.googleapis.com",
  ]
}

# --- Seed project -----------------------------------------------------------
# Created directly under the org. Run this stage as a human user (or an
# existing bootstrap identity) who can create projects under the org.
resource "google_project" "seed" {
  name            = local.seed_project_id
  project_id      = local.seed_project_id
  org_id          = var.org_id
  billing_account = var.billing_account
  labels          = var.labels

  # Greenfield safety: don't let `terraform destroy` silently delete the
  # project that holds your state. Flip to false only when intentionally tearing down.
  deletion_policy = "PREVENT"
}

resource "google_project_service" "seed" {
  for_each = toset(local.seed_apis)

  project                    = google_project.seed.project_id
  service                    = each.value
  disable_dependent_services = false
  disable_on_destroy         = false
}
