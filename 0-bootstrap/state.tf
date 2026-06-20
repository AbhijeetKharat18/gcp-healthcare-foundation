# ---------------------------------------------------------------------------
# 0-bootstrap / state.tf
# Terraform remote state bucket, encrypted with a customer-managed key (CMEK).
# CMEK on the state bucket is a HIPAA-aligned control: state can contain
# sensitive resource metadata, so we encrypt it with our own key.
# ---------------------------------------------------------------------------

# --- KMS keyring + key dedicated to protecting Terraform state --------------
resource "google_kms_key_ring" "tfstate" {
  project  = google_project.seed.project_id
  name     = "${var.project_prefix}-tfstate-ring"
  location = var.default_region

  depends_on = [google_project_service.seed]
}

resource "google_kms_crypto_key" "tfstate" {
  name            = "${var.project_prefix}-tfstate-key"
  key_ring        = google_kms_key_ring.tfstate.id
  rotation_period = "7776000s" # 90 days

  lifecycle {
    prevent_destroy = false # set true in production
  }
}

# Allow the GCS service agent to use the key for bucket encryption.
data "google_storage_project_service_account" "gcs" {
  project    = google_project.seed.project_id
  depends_on = [google_project_service.seed]
}

resource "google_kms_crypto_key_iam_member" "gcs_state" {
  crypto_key_id = google_kms_crypto_key.tfstate.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:${data.google_storage_project_service_account.gcs.email_address}"
}

# --- State bucket -----------------------------------------------------------
resource "google_storage_bucket" "tfstate" {
  project                     = google_project.seed.project_id
  name                        = "${local.seed_project_id}-tfstate"
  location                    = var.state_bucket_location
  force_destroy               = false
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  versioning {
    enabled = true
  }

  encryption {
    default_kms_key_name = google_kms_crypto_key.tfstate.id
  }

  labels = var.labels

  depends_on = [google_kms_crypto_key_iam_member.gcs_state]
}
