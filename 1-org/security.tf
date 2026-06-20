# ---------------------------------------------------------------------------
# 1-org / security.tf
# Security Command Center findings export + Essential Contacts.
# Maps to: Security Command Center / "Threat detection, findings" band, and
# OIG "response to detected offenses" + "effective lines of communication".
# ---------------------------------------------------------------------------

# --- SCC active findings -> Pub/Sub (for SIEM / alerting) -------------------
resource "google_pubsub_topic" "scc_findings" {
  project    = google_project.logging.project_id
  name       = "scc-active-findings"
  depends_on = [google_project_service.logging]
}

resource "google_scc_notification_config" "active_findings" {
  config_id    = "active-findings"
  organization = local.org_id
  description  = "Streams active SCC findings to Pub/Sub for alerting/SIEM."
  pubsub_topic = google_pubsub_topic.scc_findings.id

  streaming_config {
    filter = "state = \"ACTIVE\""
  }
}

# --- Essential Contacts (who Google notifies about security/incidents) ------
resource "google_essential_contacts_contact" "security" {
  parent                              = "organizations/${local.org_id}"
  email                               = var.security_contact_email
  language_tag                        = "en-US"
  notification_category_subscriptions = ["SECURITY", "TECHNICAL", "SUSPENSION"]
}
