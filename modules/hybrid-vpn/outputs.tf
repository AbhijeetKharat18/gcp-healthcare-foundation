# modules/hybrid-vpn/outputs.tf
output "ha_vpn_gateway_id" { value = google_compute_ha_vpn_gateway.gw.id }
output "tunnel_names"      { value = [for t in google_compute_vpn_tunnel.tunnel : t.name] }
