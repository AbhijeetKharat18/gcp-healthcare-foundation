# 2-environments / providers.tf
# user_project_override + billing_project let global APIs (billing budgets)
# bill quota to the seed project while we impersonate the foundation SA.
provider "google" {
  impersonate_service_account = local.tf_sa
  region                      = local.region
  billing_project             = local.seed_project
  user_project_override       = true
}
