# ---------------------------------------------------------------------------
# 3-networks / main.tf
# Instantiate the per-environment Shared VPC network for each env folder.
# ---------------------------------------------------------------------------

locals {
  # full env name -> on-prem CIDRs (empty if VPN not configured for that env)
  onprem_by_full = {
    for full, short in var.env_short_map :
    full => try(var.vpn_config[short].onprem_cidrs, [])
  }
}

module "net" {
  source   = "../modules/net-env"
  for_each = local.env_folder_ids

  prefix          = local.prefix
  env_short       = var.env_short_map[each.key]
  folder_id       = each.value
  billing_account = local.billing_account
  region          = local.region
  cidr            = var.cidr_plan[var.env_short_map[each.key]]
  onprem_cidrs    = local.onprem_by_full[each.key]
}
