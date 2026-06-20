# 6-monitoring / remote-state.tf
data "terraform_remote_state" "bootstrap" {
  backend = "gcs"
  config  = { bucket = var.bootstrap_state_bucket, prefix = "bootstrap" }
}
data "terraform_remote_state" "org" {
  backend = "gcs"
  config  = { bucket = var.bootstrap_state_bucket, prefix = "org" }
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
  region          = data.terraform_remote_state.bootstrap.outputs.default_region
  tf_sa           = data.terraform_remote_state.bootstrap.outputs.terraform_sa_email
  org_id          = data.terraform_remote_state.bootstrap.outputs.org_id
  logging_project = data.terraform_remote_state.org.outputs.logging_project_id
  envs_meta       = data.terraform_remote_state.environments.outputs.environments
  projects        = data.terraform_remote_state.projects.outputs.projects
  envs            = keys(data.terraform_remote_state.projects.outputs.projects)
}
