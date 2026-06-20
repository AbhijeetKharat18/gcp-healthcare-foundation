# 5-healthcare-workload / remote-state.tf
data "terraform_remote_state" "bootstrap" {
  backend = "gcs"
  config  = { bucket = var.bootstrap_state_bucket, prefix = "bootstrap" }
}
data "terraform_remote_state" "environments" {
  backend = "gcs"
  config  = { bucket = var.bootstrap_state_bucket, prefix = "environments" }
}
data "terraform_remote_state" "projects" {
  backend = "gcs"
  config  = { bucket = var.bootstrap_state_bucket, prefix = "projects" }
}

locals {
  prefix = data.terraform_remote_state.bootstrap.outputs.project_prefix
  region = data.terraform_remote_state.bootstrap.outputs.default_region
  tf_sa  = data.terraform_remote_state.bootstrap.outputs.terraform_sa_email

  # env_short -> { base_project_id, kms_key_id, ... }
  envs_meta = data.terraform_remote_state.environments.outputs.environments
  # env_short -> component -> { project_id, project_number }
  projects = data.terraform_remote_state.projects.outputs.projects

  envs = keys(local.projects)
}
