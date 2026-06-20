# 5-healthcare-workload / providers.tf
provider "google" {
  impersonate_service_account = local.tf_sa
  region                      = local.region
}
provider "google-beta" {
  impersonate_service_account = local.tf_sa
  region                      = local.region
}
