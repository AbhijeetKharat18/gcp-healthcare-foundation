# modules/hybrid-vpn/variables.tf
variable "project"          { type = string }
variable "region"           { type = string }
variable "network_id"       { type = string }
variable "env_short"        { type = string }

variable "peer_gateway_ips" {
  description = "1 or 2 public IPs of the on-prem/peer VPN device."
  type        = list(string)
}

variable "peer_asn" {
  description = "BGP ASN of the peer (on-prem) router."
  type        = number
}

variable "cloud_router_asn" {
  description = "BGP ASN for the Google Cloud Router."
  type        = number
  default     = 64514
}

variable "shared_secret" {
  description = "Pre-shared key for the VPN tunnels (use a secret, not literals)."
  type        = string
  sensitive   = true
}
