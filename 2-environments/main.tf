# ---------------------------------------------------------------------------
# 2-environments / main.tf
# Instantiate the per-environment baseline (base project + CMEK + budget)
# for every environment folder created in 1-org.
# ---------------------------------------------------------------------------

module "env" {
  source   = "../modules/env-baseline"
  for_each = local.env_folder_ids

  prefix          = local.prefix
  env             = each.key
  env_short       = var.env_short_map[each.key]
  folder_id       = each.value
  billing_account = local.billing_account
  region          = local.region
  budget_amount   = var.budget_amounts[var.env_short_map[each.key]]
}
