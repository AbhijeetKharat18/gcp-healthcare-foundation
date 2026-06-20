# ---------------------------------------------------------------------------
# modules/hybrid-vpn/main.tf
# HA VPN (two tunnels, BGP) from an environment's Shared VPC to an on-prem /
# external peer — the "Encrypted VPN/Interconnect" link in the diagrams.
# For Dedicated/Partner Interconnect, swap this for google_compute_interconnect_*
# (requires a physical/partner circuit) — documented in the stage README.
# ---------------------------------------------------------------------------

resource "google_compute_ha_vpn_gateway" "gw" {
  project = var.project
  region  = var.region
  name    = "havpn-${var.env_short}"
  network = var.network_id
}

# Peer (on-prem) gateway definition.
resource "google_compute_external_vpn_gateway" "peer" {
  project         = var.project
  name            = "peer-gw-${var.env_short}"
  redundancy_type = length(var.peer_gateway_ips) > 1 ? "TWO_IPS_REDUNDANCY" : "SINGLE_IP_INTERNALLY_REDUNDANT"

  dynamic "interface" {
    for_each = var.peer_gateway_ips
    content {
      id         = interface.key
      ip_address = interface.value
    }
  }
}

# Dedicated Cloud Router for VPN BGP sessions.
resource "google_compute_router" "vpn" {
  project = var.project
  region  = var.region
  name    = "rtr-vpn-${var.env_short}"
  network = var.network_id

  bgp {
    asn = var.cloud_router_asn
  }
}

# Two tunnels for HA (each to a peer interface; falls back to peer 0 if single).
resource "google_compute_vpn_tunnel" "tunnel" {
  for_each = toset(["0", "1"])

  project                         = var.project
  region                          = var.region
  name                            = "tun-${var.env_short}-${each.key}"
  vpn_gateway                     = google_compute_ha_vpn_gateway.gw.id
  vpn_gateway_interface           = tonumber(each.key)
  peer_external_gateway           = google_compute_external_vpn_gateway.peer.id
  peer_external_gateway_interface = length(var.peer_gateway_ips) > 1 ? tonumber(each.key) : 0
  shared_secret                   = var.shared_secret
  router                          = google_compute_router.vpn.id
}

resource "google_compute_router_interface" "vpn" {
  for_each = google_compute_vpn_tunnel.tunnel

  project    = var.project
  region     = var.region
  name       = "if-${var.env_short}-${each.key}"
  router     = google_compute_router.vpn.name
  ip_range   = "169.254.${each.key}.1/30"
  vpn_tunnel = each.value.name
}

resource "google_compute_router_peer" "vpn" {
  for_each = google_compute_router_interface.vpn

  project         = var.project
  region          = var.region
  name            = "peer-${var.env_short}-${each.key}"
  router          = google_compute_router.vpn.name
  interface       = each.value.name
  peer_ip_address = "169.254.${each.key}.2"
  peer_asn        = var.peer_asn
}
