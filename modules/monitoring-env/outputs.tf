# modules/monitoring-env/outputs.tf
output "notification_channel_id" { value = google_monitoring_notification_channel.ops_email.id }
output "dashboard_id"            { value = google_monitoring_dashboard.env.id }
