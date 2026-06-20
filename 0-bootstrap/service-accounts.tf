# ---------------------------------------------------------------------------
# 0-bootstrap / service-accounts.tf
# The Terraform service account that later stages (1-org .. 5-workload) run as.
#
# It is granted org-level roles so it can build folders, projects, policies,
# networking, and VPC-SC. This is powerful; in production you would scope this
# down per-stage. For a lean greenfield reference we use one foundation SA.
# ---------------------------------------------------------------------------

resource "google_service_account" "terraform" {
  project      = google_project.seed.project_id
  account_id   = "sa-terraform-foundation"
  display_name = "Terraform Foundation (runs stages 1-5)"
}

# Org-level roles required to terraform the foundation.
locals {
  org_roles = [
    "roles/resourcemanager.organizationViewer",
    "roles/resourcemanager.folderAdmin",
    "roles/resourcemanager.projectCreator",
    "roles/resourcemanager.projectDeleter",
    "roles/orgpolicy.policyAdmin",
    "roles/billing.user",
    "roles/logging.configWriter",
    "roles/compute.xpnAdmin",                  # shared VPC host enablement
    "roles/accesscontextmanager.policyAdmin",  # VPC-SC perimeters
    "roles/securitycenter.admin",              # SCC config
    "roles/iam.organizationRoleAdmin",
    "roles/serviceusage.serviceUsageAdmin",
  ]
}

resource "google_organization_iam_member" "terraform_sa" {
  for_each = toset(local.org_roles)

  org_id = var.org_id
  role   = each.value
  member = "serviceAccount:${google_service_account.terraform.email}"
}

# Billing access so the SA can attach billing to projects it creates.
resource "google_billing_account_iam_member" "terraform_sa" {
  billing_account_id = var.billing_account
  role               = "roles/billing.user"
  member             = "serviceAccount:${google_service_account.terraform.email}"
}

# --- Break-glass / human admin groups --------------------------------------
resource "google_organization_iam_member" "org_admins" {
  org_id = var.org_id
  role   = "roles/resourcemanager.organizationAdmin"
  member = "group:${var.org_admins_group}"
}

resource "google_billing_account_iam_member" "billing_admins" {
  billing_account_id = var.billing_account
  role               = "roles/billing.admin"
  member             = "group:${var.billing_admins_group}"
}

# Let the org-admins group impersonate the Terraform SA (how operators run TF).
resource "google_service_account_iam_member" "impersonation" {
  service_account_id = google_service_account.terraform.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "group:${var.org_admins_group}"
}
