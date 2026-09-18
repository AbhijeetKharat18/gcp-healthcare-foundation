# poc/nl-analytics-assistant/terraform/providers.tf
# Operators impersonate the foundation Terraform SA; no SA keys (repo convention).
provider "google" {
  impersonate_service_account = local.tf_sa
  region                      = local.region
}
