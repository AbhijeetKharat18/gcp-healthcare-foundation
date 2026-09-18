# poc/nl-analytics-assistant/terraform/outputs.tf
output "service_uri" {
  description = "Cloud Run URL of the assistant (reachable from inside the perimeter)."
  value       = google_cloud_run_v2_service.assistant.uri
}

output "service_name" {
  value = google_cloud_run_v2_service.assistant.name
}

output "runtime_service_account" {
  description = "The identity the service runs as (secure_views read-only + Vertex + BQ jobs)."
  value       = local.delivery_sa
}
