# 2-environments / backend.tf
terraform {
  backend "gcs" {
    bucket = "hcf-b-seed-tfstate" # = 0-bootstrap output tfstate_bucket
    prefix = "environments"
  }
}
