# 4-projects / backend.tf
terraform {
  backend "gcs" {
    bucket = "hcf-b-seed-tfstate"
    prefix = "projects"
  }
}
