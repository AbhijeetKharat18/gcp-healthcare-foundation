# modules/monitoring-env/variables.tf
variable "env_short"             { type = string }
variable "scoping_project_id"    { type = string }
variable "monitored_project_ids" { type = list(string) }
variable "alert_email"           { type = string }
