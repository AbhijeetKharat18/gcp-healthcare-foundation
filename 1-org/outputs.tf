# ---------------------------------------------------------------------------
# 1-org / outputs.tf
# Folder IDs feed stage 2 (environments) and stage 4 (projects).
# ---------------------------------------------------------------------------

output "common_folder_id" {
  description = "Folder ID (folders/NNN) for shared/common resources."
  value       = google_folder.common.name
}

output "environment_folder_ids" {
  description = "Map of environment name -> folder name (folders/NNN)."
  value       = { for k, f in google_folder.environments : k => f.name }
}

output "logging_project_id" {
  description = "Central logging project."
  value       = google_project.logging.project_id
}

output "audit_archive_bucket" {
  description = "Immutable audit-log archive bucket."
  value       = google_storage_bucket.audit_logs.name
}

output "scc_findings_topic" {
  value = google_pubsub_topic.scc_findings.id
}
