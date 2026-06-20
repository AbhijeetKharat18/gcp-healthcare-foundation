# ---------------------------------------------------------------------------
# 3-networks / main.tf
# Instantiate the per-environment Shared VPC network for each env folder.
# ---------------------------------------------------------------------------

module "net" {
  source   = "../modules/net-env"
  for_each = local.env_folder_ids

  prefix          = local.prefix
  env_short       = var.env_short_map[each.key]
  folder_id       = each.value
  billing_account = local.billing_account
  region          = local.region
  cidr            = var.cidr_plan[var.env_short_map[each.key]]
}
