# 6-monitoring / outputs.tf
output "security_alert_policies" {
  description = "Security alert policy IDs."
  value       = { for k, p in google_monitoring_alert_policy.security : k => p.id }
}

output "security_metrics" {
  value = { for k, m in google_logging_metric.security : k => m.id }
}

output "env_dashboards" {
  value = { for e, m in module.monitoring : e => m.dashboard_id }
}
