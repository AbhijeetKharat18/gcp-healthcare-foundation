# ---------------------------------------------------------------------------
# 5-healthcare-workload / iam.tf
# Per-environment workload service accounts with least-privilege roles. These
# are the runtime identities for the ingestion adapter, the harmonization/de-id
# pipelines, and the delivery layer (Cloud Run / APIs).
# ---------------------------------------------------------------------------

# --- Ingestion SA (MLLP adapter / loaders) ----------------------------------
resource "google_service_account" "ingestion" {
  for_each     = toset(local.envs)
  project      = local.projects[each.key]["ingestion"].project_id
  account_id   = "sa-ingestion"
  display_name = "Ingestion runtime (${each.key})"
}

resource "google_healthcare_dataset_iam_member" "ingestion_editor" {
  for_each   = toset(local.envs)
  dataset_id = google_healthcare_dataset.main[each.key].id
  role       = "roles/healthcare.datasetAdmin"
  member     = "serviceAccount:${google_service_account.ingestion[each.key].email}"
}

resource "google_storage_bucket_iam_member" "ingestion_landing" {
  for_each = toset(local.envs)
  bucket   = google_storage_bucket.landing[each.key].name
  role     = "roles/storage.objectAdmin"
  member   = "serviceAccount:${google_service_account.ingestion[each.key].email}"
}

# --- Pipeline SA (harmonization + DLP de-identification) --------------------
resource "google_service_account" "pipeline" {
  for_each     = toset(local.envs)
  project      = local.projects[each.key]["lakehouse"].project_id
  account_id   = "sa-pipeline"
  display_name = "Harmonization/DLP pipeline (${each.key})"
}

resource "google_project_iam_member" "pipeline_roles" {
  for_each = {
    for pair in setproduct(local.envs, [
      "roles/bigquery.dataEditor",
      "roles/bigquery.jobUser",
      "roles/dlp.user",
      "roles/dataflow.worker",
    ]) : "${pair[0]}-${pair[1]}" => { env = pair[0], role = pair[1] }
  }

  project = local.projects[each.value.env]["lakehouse"].project_id
  role    = each.value.role
  member  = "serviceAccount:${google_service_account.pipeline[each.value.env].email}"
}

# Pipeline reads source records from the Healthcare dataset.
resource "google_healthcare_dataset_iam_member" "pipeline_reader" {
  for_each   = toset(local.envs)
  dataset_id = google_healthcare_dataset.main[each.key].id
  role       = "roles/healthcare.datasetViewer"
  member     = "serviceAccount:${google_service_account.pipeline[each.key].email}"
}

# --- Delivery SA (Cloud Run / API Gateway) ----------------------------------
resource "google_service_account" "delivery" {
  for_each     = toset(local.envs)
  project      = local.projects[each.key]["delivery"].project_id
  account_id   = "sa-delivery"
  display_name = "Delivery APIs (${each.key})"
}

# Delivery reads only governed secure_views, never raw PHI.
resource "google_bigquery_dataset_iam_member" "delivery_secure_views" {
  for_each   = toset(local.envs)
  project    = local.projects[each.key]["lakehouse"].project_id
  dataset_id = google_bigquery_dataset.medallion["${each.key}-secure_views"].dataset_id
  role       = "roles/bigquery.dataViewer"
  member     = "serviceAccount:${google_service_account.delivery[each.key].email}"
}
