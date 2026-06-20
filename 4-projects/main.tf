# ---------------------------------------------------------------------------
# 4-projects / main.tf
# Build the full env x component matrix of workload projects, then add each
# to its environment's VPC-SC perimeter.
# ---------------------------------------------------------------------------

locals {
  # Flatten {env_full -> short} x {component -> apis} into one keyed map:
  #   "dev-ingestion" => { env_short, folder_id, component, apis }
  env_components = merge([
    for env_full, short in var.env_short_map : {
      for comp, apis in var.components :
      "${short}-${comp}" => {
        env_short = short
        folder_id = local.env_folder_ids[env_full]
        component = comp
        apis      = apis
      }
    }
  ]...)
}

module "project" {
  source   = "../modules/workload-project"
  for_each = local.env_components

  prefix          = local.prefix
  env_short       = each.value.env_short
  component       = each.value.component
  folder_id       = each.value.folder_id
  billing_account = local.billing_account
  region          = local.region
  host_project_id = local.networks[each.value.env_short].host_project_id
  subnet_name     = local.networks[each.value.env_short].subnet_name
  apis            = each.value.apis
}

# --- Add each workload project to its env VPC-SC perimeter -------------------
resource "google_access_context_manager_service_perimeter_resource" "members" {
  for_each = local.env_components

  perimeter_name = local.perimeter_names[each.value.env_short]
  resource       = "projects/${module.project[each.key].project_number}"
}
