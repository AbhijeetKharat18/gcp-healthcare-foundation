# 5-healthcare-workload / backend.tf
terraform {
  backend "gcs" {
    bucket = "hcf-b-seed-tfstate"
    prefix = "healthcare-workload"
  }
}
