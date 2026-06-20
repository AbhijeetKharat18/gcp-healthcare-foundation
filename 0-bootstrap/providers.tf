# ---------------------------------------------------------------------------
# 0-bootstrap / providers.tf
# Bootstrap runs as a human/operator identity (Application Default Credentials),
# because the Terraform SA it creates does not exist yet.
# ---------------------------------------------------------------------------

provider "google" {
  region = var.default_region
}

provider "google-beta" {
  region = var.default_region
}
