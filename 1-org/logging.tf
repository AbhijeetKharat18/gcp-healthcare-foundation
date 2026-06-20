# ---------------------------------------------------------------------------
# 1-org / logging.tf
# Centralized, tamper-resistant audit logging.
#   - A dedicated logging project in fldr-common.
#   - An immutable (bucket-locked) CMEK-encrypted GCS archive.
#   - An org-level aggregated sink exporting audit logs from ALL projects.
# Maps to: Audit Controls / "Immutable retention" in both diagrams, and to
# HIPAA audit-control + OIG "internal monitoring & auditing".
# ---------------------------------------------------------------------------

locals {
  logging_project_id = "${local.prefix}-c-logging" # c = common
  common_folder_id   = trimprefix(google_folder.common.name, "folders/")
}

resource "google_project" "logging" {
  name            = local.logging_project_id
  project_id      = local.logging_project_id
  folder_id       = local.common_folder_id
  billing_account = local.billing_account
  deletion_policy = "PREVENT"
  labels = {
    environment = "common"
    component   = "logging"
    managed-by  = "terraform"
  }
}

resource "google_project_service" "logging" {
  for_each = toset([
    "logging.googleapis.com",
    "storage.googleapis.com",
    "cloudkms.googleapis.com",
    "pubsub.googleapis.com",
  ])
  project            = google_project.logging.project_id
  service            = each.value
  disable_on_destroy = false
}

# --- CMEK for the audit archive (org policy requires CMEK on storage) --------
resource "google_kms_key_ring" "logs" {
  project    = google_project.logging.project_id
  name       = "${local.prefix}-logs-ring"
  location   = local.region
  depends_on = [google_project_service.logging]
}

resource "google_kms_crypto_key" "logs" {
  name            = "${local.prefix}-logs-key"
  key_ring        = google_kms_key_ring.logs.id
  rotation_period = "7776000s" # 90 days
}

data "google_storage_project_service_account" "logging" {
  project    = google_project.logging.project_id
  depends_on = [google_project_service.logging]
}

resource "google_kms_crypto_key_iam_member" "logs_gcs" {
  crypto_key_id = google_kms_crypto_key.logs.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:${data.google_storage_project_service_account.logging.email_address}"
}

# --- Immutable audit log archive bucket -------------------------------------
resource "google_storage_bucket" "audit_logs" {
  project                     = google_project.logging.project_id
  name                        = "${local.logging_project_id}-audit-archive"
  location                    = local.region
  force_destroy               = false
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  versioning { enabled = true }

  # Bucket Lock: retention is enforced and CANNOT be shortened once locked.
  retention_policy {
    is_locked        = true
    retention_period = var.audit_log_retention_days * 86400
  }

  encryption {
    default_kms_key_name = google_kms_crypto_key.logs.id
  }

  depends_on = [google_kms_crypto_key_iam_member.logs_gcs]
}

# --- Org-level aggregated audit sink ----------------------------------------
resource "google_logging_organization_sink" "audit" {
  name             = "org-audit-sink"
  org_id           = local.org_id
  include_children = true
  destination      = "storage.googleapis.com/${google_storage_bucket.audit_logs.name}"

  # Admin Activity + Data Access + System Event + Policy Denied audit logs.
  filter = "logName:\"cloudaudit.googleapis.com\""
}

# Grant the sink's writer identity permission to write to the bucket.
resource "google_storage_bucket_iam_member" "audit_sink_writer" {
  bucket = google_storage_bucket.audit_logs.name
  role   = "roles/storage.objectCreator"
  member = google_logging_organization_sink.audit.writer_identity
}
