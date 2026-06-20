# ---------------------------------------------------------------------------
# modules/monitoring-env/main.tf
# Per-environment operational monitoring: make the env base project a metrics
# scope that observes all of that environment's workload projects, add an email
# notification channel, and publish a starter dashboard.
# ---------------------------------------------------------------------------

# Add each workload project to the env base project's metrics scope.
resource "google_monitoring_monitored_project" "member" {
  for_each = toset(var.monitored_project_ids)

  metrics_scope = "locations/global/metricsScopes/${var.scoping_project_id}"
  name          = each.value
}

resource "google_monitoring_notification_channel" "ops_email" {
  project      = var.scoping_project_id
  display_name = "Ops Alerts ${var.env_short} (email)"
  type         = "email"
  labels = {
    email_address = var.alert_email
  }
}

# Starter dashboard (extend with workload-specific charts as services deploy).
resource "google_monitoring_dashboard" "env" {
  project = var.scoping_project_id

  dashboard_json = jsonencode({
    displayName = "Healthcare Platform - ${var.env_short}"
    mosaicLayout = {
      columns = 12
      tiles = [
        {
          width  = 12
          height = 2
          widget = {
            title = "Environment: ${var.env_short}"
            text = {
              content = "Operational dashboard for the ${var.env_short} environment. Metrics scope includes all ${var.env_short} workload projects (ingestion, healthcare-core, lakehouse, delivery)."
              format  = "MARKDOWN"
            }
          }
        }
      ]
    }
  })
}
