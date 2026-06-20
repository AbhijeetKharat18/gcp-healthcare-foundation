# ---------------------------------------------------------------------------
# 5-healthcare-workload / storage.tf
# GCS landing zone (Image 1 "Cloud Storage landing zone for files & extracts"),
# one CMEK-encrypted bucket per environment in the ingestion project.
# ---------------------------------------------------------------------------

data "google_storage_project_service_account" "gcs" {
  for_each = toset(local.envs)
  project  = local.projects[each.key]["ingestion"].project_id
}

resource "google_kms_crypto_key_iam_member" "gcs_cmek" {
  for_each = toset(local.envs)

  crypto_key_id = local.envs_meta[each.key].kms_key_id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:${data.google_storage_project_service_account.gcs[each.key].email_address}"
}

resource "google_storage_bucket" "landing" {
  for_each = toset(local.envs)

  project                     = local.projects[each.key]["ingestion"].project_id
  name                        = "${local.prefix}-${each.key}-landing"
  location                    = local.region
  force_destroy               = false
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  versioning { enabled = true }

  encryption {
    default_kms_key_name = local.envs_meta[each.key].kms_key_id
  }

  # Auto-expire raw extracts from the landing zone after 30 days.
  lifecycle_rule {
    condition { age = 30 }
    action { type = "Delete" }
  }

  labels = { environment = each.key, component = "ingestion-landing" }

  depends_on = [google_kms_crypto_key_iam_member.gcs_cmek]
}
