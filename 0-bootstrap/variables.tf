# ---------------------------------------------------------------------------
# 0-bootstrap / variables.tf
# All values are placeholders for greenfield. Fill terraform.tfvars before apply.
# ---------------------------------------------------------------------------

variable "org_id" {
  description = "GCP Organization ID (numeric). e.g. 123456789012"
  type        = string
}

variable "billing_account" {
  description = "Billing Account ID. e.g. ABCDEF-123456-GHIJKL"
  type        = string
}

variable "project_prefix" {
  description = "Short prefix for all generated project IDs (lowercase, <=6 chars)."
  type        = string
  default     = "hcf" # healthcare-foundation
}

variable "default_region" {
  description = "Default region for regional resources (state bucket, KMS, etc.)."
  type        = string
  default     = "us-central1"
}

variable "state_bucket_location" {
  description = "Location for the Terraform state bucket (multi-region or region)."
  type        = string
  default     = "US"
}

variable "org_admins_group" {
  description = "Google Group email granted org-level admin (break-glass / platform team)."
  type        = string
  default     = "gcp-organization-admins@example.com"
}

variable "billing_admins_group" {
  description = "Google Group email granted billing admin."
  type        = string
  default     = "gcp-billing-admins@example.com"
}

variable "labels" {
  description = "Common labels applied to bootstrap resources."
  type        = map(string)
  default = {
    environment = "bootstrap"
    managed-by  = "terraform"
    workload    = "healthcare-foundation"
  }
}
