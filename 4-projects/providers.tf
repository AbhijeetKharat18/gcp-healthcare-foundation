# 4-projects / providers.tf
provider "google" {
  impersonate_service_account = local.tf_sa
  region                      = local.region
}
