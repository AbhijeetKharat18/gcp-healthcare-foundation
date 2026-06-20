# ---------------------------------------------------------------------------
# 5-healthcare-workload / lakehouse.tf
# The BigQuery "medallion" lakehouse from Image 1, per environment, all CMEK-
# encrypted with the environment key:
#   raw_phi          -> append-only landing for FHIR stream
#   standardized_phi -> FHIR-mapped / normalized
#   curated_phi      -> business-ready, conformed
#   deidentified     -> DLP de-identified for research/ML
#   analytics_mart   -> aggregated marts / dashboards
#   secure_views     -> authorized views w/ CLS + RLS (populated in secure-views.tf)
# ---------------------------------------------------------------------------

locals {
  lakehouse_datasets = {
    raw_phi          = "Raw PHI landing (append-only) from FHIR StreamConfig."
    standardized_phi = "FHIR-mapped, normalized clinical data."
    curated_phi      = "Business-ready, conformed analytics data."
    deidentified     = "DLP de-identified data for research and ML."
    analytics_mart   = "Aggregated data marts and dashboards."
    secure_views     = "Authorized views with column- and row-level security."
  }

  env_datasets = merge([
    for env in local.envs : {
      for ds, desc in local.lakehouse_datasets :
      "${env}-${ds}" => { env = env, dataset = ds, desc = desc }
    }
  ]...)
}

# --- BigQuery service agent must be able to use the env CMEK key -------------
data "google_bigquery_default_service_account" "bq" {
  for_each = toset(local.envs)
  project  = local.projects[each.key]["lakehouse"].project_id
}

resource "google_kms_crypto_key_iam_member" "bq_cmek" {
  for_each = toset(local.envs)

  crypto_key_id = local.envs_meta[each.key].kms_key_id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:${data.google_bigquery_default_service_account.bq[each.key].email}"
}

# --- Medallion datasets -----------------------------------------------------
resource "google_bigquery_dataset" "medallion" {
  for_each = local.env_datasets

  project       = local.projects[each.value.env]["lakehouse"].project_id
  dataset_id    = each.value.dataset
  friendly_name = each.value.dataset
  description   = each.value.desc
  location      = local.region

  default_encryption_configuration {
    kms_key_name = local.envs_meta[each.value.env].kms_key_id
  }

  labels = {
    environment = each.value.env
    tier        = each.value.dataset
  }

  depends_on = [google_kms_crypto_key_iam_member.bq_cmek]
}
