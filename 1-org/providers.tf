# ---------------------------------------------------------------------------
# 1-org / providers.tf
# Run as the foundation SA via impersonation (operators never use SA keys).
# ---------------------------------------------------------------------------
provider "google" {
  impersonate_service_account = local.tf_sa
  region                      = local.region
}

provider "google-beta" {
  impersonate_service_account = local.tf_sa
  region                      = local.region
}
