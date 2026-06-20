# 6-monitoring / backend.tf
terraform {
  backend "gcs" {
    bucket = "hcf-b-seed-tfstate"
    prefix = "monitoring"
  }
}
