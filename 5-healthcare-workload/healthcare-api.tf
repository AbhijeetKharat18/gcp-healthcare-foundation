# ---------------------------------------------------------------------------
# 5-healthcare-workload / healthcare-api.tf
# Cloud Healthcare API: one dataset per env with FHIR R4, HL7v2, and DICOM
# stores. Each store emits Pub/Sub notifications (CMEK-encrypted). The FHIR
# store streams into the raw_phi BigQuery dataset (the diagram's StreamConfig).
# ---------------------------------------------------------------------------

# --- Pub/Sub notification plumbing (CMEK) -----------------------------------
resource "google_project_service_identity" "pubsub" {
  provider = google-beta
  for_each = toset(local.envs)
  project  = local.projects[each.key]["healthcare-core"].project_id
  service  = "pubsub.googleapis.com"
}

resource "google_kms_crypto_key_iam_member" "pubsub_cmek" {
  for_each = toset(local.envs)

  crypto_key_id = local.envs_meta[each.key].kms_key_id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:${google_project_service_identity.pubsub[each.key].email}"
}

locals {
  notification_stores = ["fhir", "hl7v2", "dicom"]

  env_topics = merge([
    for env in local.envs : {
      for store in local.notification_stores :
      "${env}-${store}" => { env = env, store = store }
    }
  ]...)
}

resource "google_pubsub_topic" "notify" {
  for_each = local.env_topics

  project      = local.projects[each.value.env]["healthcare-core"].project_id
  name         = "hc-notify-${each.value.store}"
  kms_key_name = local.envs_meta[each.value.env].kms_key_id

  depends_on = [google_kms_crypto_key_iam_member.pubsub_cmek]
}

# --- Healthcare dataset ------------------------------------------------------
# NOTE: CMEK for Healthcare is set via the dataset encryptionSpec API, which the
# Terraform provider does not expose. Configure it out-of-band, then add
# healthcare.googleapis.com back to the CMEK-required org policy (see 1-org).
resource "google_healthcare_dataset" "main" {
  for_each = toset(local.envs)

  project   = local.projects[each.key]["healthcare-core"].project_id
  name      = "${local.prefix}-${each.key}-hcds"
  location  = local.region
  time_zone = "UTC"
}

# Healthcare service agent (for FHIR -> BigQuery streaming).
resource "google_project_service_identity" "healthcare" {
  provider = google-beta
  for_each = toset(local.envs)
  project  = local.projects[each.key]["healthcare-core"].project_id
  service  = "healthcare.googleapis.com"
}

# Allow the Healthcare agent to write streamed FHIR into raw_phi.
resource "google_bigquery_dataset_iam_member" "healthcare_stream_writer" {
  for_each = toset(local.envs)

  project    = local.projects[each.key]["lakehouse"].project_id
  dataset_id = google_bigquery_dataset.medallion["${each.key}-raw_phi"].dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_project_service_identity.healthcare[each.key].email}"
}

resource "google_project_iam_member" "healthcare_bq_jobuser" {
  for_each = toset(local.envs)

  project = local.projects[each.key]["lakehouse"].project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_project_service_identity.healthcare[each.key].email}"
}

# --- FHIR R4 store (with notifications + BigQuery streaming) -----------------
resource "google_healthcare_fhir_store" "fhir" {
  for_each = toset(local.envs)

  name    = "fhir-r4"
  dataset = google_healthcare_dataset.main[each.key].id
  version = "R4"

  enable_update_create          = true
  disable_referential_integrity = false

  notification_configs {
    pubsub_topic = google_pubsub_topic.notify["${each.key}-fhir"].id
  }

  stream_configs {
    bigquery_destination {
      dataset_uri = "bq://${local.projects[each.key]["lakehouse"].project_id}.raw_phi"
      schema_config {
        recursive_structure_depth = 3
        schema_type               = "ANALYTICS_V2"
      }
    }
  }

  depends_on = [
    google_bigquery_dataset_iam_member.healthcare_stream_writer,
    google_project_iam_member.healthcare_bq_jobuser,
  ]
}

# --- HL7v2 store ------------------------------------------------------------
resource "google_healthcare_hl7_v2_store" "hl7" {
  for_each = toset(local.envs)

  name    = "hl7v2"
  dataset = google_healthcare_dataset.main[each.key].id

  notification_configs {
    pubsub_topic = google_pubsub_topic.notify["${each.key}-hl7v2"].id
  }
}

# --- DICOM store ------------------------------------------------------------
resource "google_healthcare_dicom_store" "dicom" {
  for_each = toset(local.envs)

  name    = "dicom"
  dataset = google_healthcare_dataset.main[each.key].id

  notification_config {
    pubsub_topic = google_pubsub_topic.notify["${each.key}-dicom"].id
  }
}
