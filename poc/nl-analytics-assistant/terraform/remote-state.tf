# poc/nl-analytics-assistant/terraform/remote-state.tf
# Read the foundation's outputs so the POC wires itself to the real projects and
# the existing sa-delivery identity, exactly like the numbered stages do.
data "terraform_remote_state" "bootstrap" {
  backend = "gcs"
  config  = { bucket = var.bootstrap_state_bucket, prefix = "bootstrap" }
}

data "terraform_remote_state" "projects" {
  backend = "gcs"
  config  = { bucket = var.bootstrap_state_bucket, prefix = "projects" }
}

data "terraform_remote_state" "workload" {
  backend = "gcs"
  config  = { bucket = var.bootstrap_state_bucket, prefix = "healthcare-workload" }
}

locals {
  prefix = data.terraform_remote_state.bootstrap.outputs.project_prefix
  region = data.terraform_remote_state.bootstrap.outputs.default_region
  tf_sa  = data.terraform_remote_state.bootstrap.outputs.terraform_sa_email

  # env_short -> component -> { project_id, project_number }
  projects = data.terraform_remote_state.projects.outputs.projects

  # env_short -> { ingestion, pipeline, delivery } service-account emails
  workload_sas = data.terraform_remote_state.workload.outputs.workload_service_accounts

  delivery_project_id  = local.projects[var.target_env]["delivery"].project_id
  lakehouse_project_id = local.projects[var.target_env]["lakehouse"].project_id
  delivery_sa          = local.workload_sas[var.target_env].delivery
}
