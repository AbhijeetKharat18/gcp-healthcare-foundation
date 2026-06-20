# ---------------------------------------------------------------------------
# 1-org / remote-state.tf
# Pull org settings + the Terraform SA from 0-bootstrap.
# ---------------------------------------------------------------------------
data "terraform_remote_state" "bootstrap" {
  backend = "gcs"
  config = {
    bucket = var.bootstrap_state_bucket
    prefix = "bootstrap"
  }
}

locals {
  org_id          = data.terraform_remote_state.bootstrap.outputs.org_id
  billing_account = data.terraform_remote_state.bootstrap.outputs.billing_account
  prefix          = data.terraform_remote_state.bootstrap.outputs.project_prefix
  region          = data.terraform_remote_state.bootstrap.outputs.default_region
  tf_sa           = data.terraform_remote_state.bootstrap.outputs.terraform_sa_email
}
