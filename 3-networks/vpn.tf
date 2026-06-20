# ---------------------------------------------------------------------------
# 3-networks / vpn.tf
# Optional HA VPN to on-prem per environment. Empty by default (greenfield).
# Populate var.vpn_config to enable for an environment.
# ---------------------------------------------------------------------------

locals {
  # short code -> net module outputs (for VPN wiring)
  net_by_short = {
    for full, short in var.env_short_map :
    short => module.net[full]
  }
}

module "hybrid_vpn" {
  source   = "../modules/hybrid-vpn"
  for_each = var.vpn_config

  env_short        = each.key
  project          = local.net_by_short[each.key].host_project_id
  network_id       = local.net_by_short[each.key].network_id
  region           = local.region
  peer_gateway_ips = each.value.peer_gateway_ips
  peer_asn         = each.value.peer_asn
  shared_secret    = each.value.shared_secret
}
