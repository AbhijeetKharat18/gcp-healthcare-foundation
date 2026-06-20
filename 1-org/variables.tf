# ---------------------------------------------------------------------------
# 1-org / variables.tf
# Most org-wide settings are read from 0-bootstrap remote state.
# These are the few things specific to org configuration.
# ---------------------------------------------------------------------------

variable "bootstrap_state_bucket" {
  description = "GCS bucket holding 0-bootstrap state (output tfstate_bucket)."
  type        = string
}

variable "environments" {
  description = "Environment folders to create under the org."
  type        = list(string)
  default     = ["development", "nonproduction", "production"]
}

variable "allowed_locations" {
  description = "Allowed GCP resource locations (org policy gcp.resourceLocations)."
  type        = list(string)
  # Keep PHI in-country. US-only by default; tighten/loosen per your data residency needs.
  default     = ["in:us-locations"]
}

variable "cmek_required_services" {
  description = "Services that must use CMEK (org policy gcp.restrictNonCmekServices)."
  type        = list(string)
  default = [
    "bigquery.googleapis.com",
    "storage.googleapis.com",
    "pubsub.googleapis.com",
    # NOTE: healthcare.googleapis.com is intentionally omitted. The Terraform
    # google_healthcare_dataset resource cannot set CMEK (no encryption_spec),
    # so requiring it org-wide would block dataset creation. Configure Healthcare
    # CMEK via the dataset encryptionSpec API/gcloud, then add it here.
  ]
}

variable "security_contact_email" {
  description = "Essential Contacts email for security notifications."
  type        = string
  default     = "security-alerts@example.com"
}

variable "audit_log_retention_days" {
  description = "Locked retention (days) for the immutable audit log archive bucket."
  type        = number
  default     = 2555 # ~7 years, common HIPAA-aligned retention
}
