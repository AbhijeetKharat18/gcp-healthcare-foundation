# 3-networks / backend.tf
terraform {
  backend "gcs" {
    bucket = "hcf-b-seed-tfstate"
    prefix = "networks"
  }
}
