# ---------------------------------------------------------------------------
# 6-monitoring / central-security.tf
# Org-wide security alerting. An aggregated org sink routes audit logs into the
# logging project so log-based metrics there see ALL projects; metrics feed
# alert policies that notify on sensitive events. Maps to OIG "internal
# monitoring" + "response to detected offenses" and the Cloud Monitoring band.
# ---------------------------------------------------------------------------

# Route all child audit logs into the logging project's _Default bucket so
# log-based metrics below can match across the whole org.
resource "google_logging_organization_sink" "security" {
  name             = "org-security-to-logbucket"
  org_id           = local.org_id
  include_children = true
  destination      = "logging.googleapis.com/projects/${local.logging_project}/locations/global/buckets/_Default"
  filter           = "logName:\"cloudaudit.googleapis.com\""
}

resource "google_project_iam_member" "security_sink_writer" {
  project = local.logging_project
  role    = "roles/logging.bucketWriter"
  member  = google_logging_organization_sink.security.writer_identity
}

# --- Notification channel ---------------------------------------------------
resource "google_monitoring_notification_channel" "security_email" {
  project      = local.logging_project
  display_name = "Security Alerts (email)"
  type         = "email"
  labels = {
    email_address = var.alert_email
  }
}

# --- Log-based metrics on sensitive audit events ----------------------------
locals {
  security_metrics = {
    iam_policy_changes = {
      desc   = "Count of SetIamPolicy calls."
      filter = "protoPayload.methodName=\"SetIamPolicy\""
    }
    vpcsc_violations = {
      desc   = "VPC Service Controls denied requests."
      filter = "protoPayload.metadata.@type=\"type.googleapis.com/google.cloud.audit.VpcServiceControlAuditMetadata\""
    }
    sa_key_created = {
      desc   = "Service account key creation events."
      filter = "protoPayload.methodName=\"google.iam.admin.v1.CreateServiceAccountKey\""
    }
    kms_key_destroy = {
      desc   = "Scheduled destruction of a KMS key version."
      filter = "protoPayload.methodName:\"DestroyCryptoKeyVersion\""
    }
  }
}

resource "google_logging_metric" "security" {
  for_each = local.security_metrics

  project = local.logging_project
  name    = each.key
  filter  = each.value.filter

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
}

# --- Alert policies: fire when any of these events occur ---------------------
resource "google_monitoring_alert_policy" "security" {
  for_each = local.security_metrics

  project      = local.logging_project
  display_name = "SECURITY: ${each.key}"
  combiner     = "OR"

  conditions {
    display_name = "${each.key} > 0"
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/${each.key}\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      duration        = "0s"

      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_DELTA"
      }

      trigger {
        count = 1
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.security_email.id]

  documentation {
    content   = "Security event detected: ${each.value.desc} Investigate in Cloud Logging / SCC."
    mime_type = "text/markdown"
  }

  depends_on = [google_logging_metric.security]
}
