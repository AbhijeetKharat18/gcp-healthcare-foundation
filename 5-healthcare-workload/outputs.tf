# 5-healthcare-workload / outputs.tf
output "healthcare_datasets" {
  description = "Healthcare dataset IDs by environment."
  value       = { for e, d in google_healthcare_dataset.main : e => d.id }
}

output "fhir_stores" {
  value = { for e, s in google_healthcare_fhir_store.fhir : e => s.id }
}

output "lakehouse_datasets" {
  description = "Medallion dataset IDs keyed by env-tier."
  value       = { for k, d in google_bigquery_dataset.medallion : k => d.id }
}

output "landing_buckets" {
  value = { for e, b in google_storage_bucket.landing : e => b.name }
}

output "dlp_deidentify_templates" {
  value = { for e, t in google_data_loss_prevention_deidentify_template.phi : e => t.id }
}

output "phi_taxonomies" {
  value = { for e, t in google_data_catalog_taxonomy.phi : e => t.id }
}

output "workload_service_accounts" {
  value = {
    for e in local.envs : e => {
      ingestion = google_service_account.ingestion[e].email
      pipeline  = google_service_account.pipeline[e].email
      delivery  = google_service_account.delivery[e].email
    }
  }
}
