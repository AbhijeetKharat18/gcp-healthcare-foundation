# 4-projects / remote-state.tf
data "terraform_remote_state" "bootstrap" {
  backend = "gcs"
  config  = { bucket = var.bootstrap_state_bucket, prefix = "bootstrap" }
}
data "terraform_remote_state" "org" {
  backend = "gcs"
  config  = { bucket = var.bootstrap_state_bucket, prefix = "org" }
}
data "terraform_remote_state" "networks" {
  backend = "gcs"
  config  = { bucket = var.bootstrap_state_bucket, prefix = "networks" }
}

locals {
  billing_account = data.terraform_remote_state.bootstrap.outputs.billing_account
  prefix          = data.terraform_remote_state.bootstrap.outputs.project_prefix
  region          = data.terraform_remote_state.bootstrap.outputs.default_region
  tf_sa           = data.terraform_remote_state.bootstrap.outputs.terraform_sa_email

  env_folder_ids = {
    for env, folder in data.terraform_remote_state.org.outputs.environment_folder_ids :
    env => trimprefix(folder, "folders/")
  }

  networks        = data.terraform_remote_state.networks.outputs.networks
  perimeter_names = data.terraform_remote_state.networks.outputs.perimeter_names
}
