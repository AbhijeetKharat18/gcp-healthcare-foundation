# ---------------------------------------------------------------------------
# 1-org / backend.tf
# Remote state in the bucket created by 0-bootstrap.
# Set the bucket name to 0-bootstrap output `tfstate_bucket`.
# ---------------------------------------------------------------------------
terraform {
  backend "gcs" {
    bucket = "hcf-b-seed-tfstate" # = 0-bootstrap output tfstate_bucket
    prefix = "org"
  }
}
