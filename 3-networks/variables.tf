# ---------------------------------------------------------------------------
# 3-networks / variables.tf
# ---------------------------------------------------------------------------

variable "bootstrap_state_bucket" {
  type = string
}

variable "env_short_map" {
  type = map(string)
  default = {
    development   = "dev"
    nonproduction = "nonprod"
    production    = "prod"
  }
}

# Non-overlapping CIDR plan per environment (keyed by short code).
variable "cidr_plan" {
  type = map(object({
    primary  = string
    pods     = string
    services = string
  }))
  default = {
    dev = {
      primary  = "10.10.0.0/20"
      pods     = "10.20.0.0/16"
      services = "10.30.0.0/20"
    }
    nonprod = {
      primary  = "10.11.0.0/20"
      pods     = "10.21.0.0/16"
      services = "10.31.0.0/20"
    }
    prod = {
      primary  = "10.12.0.0/20"
      pods     = "10.22.0.0/16"
      services = "10.32.0.0/20"
    }
  }
}

# Services that must only be reachable inside a VPC-SC perimeter.
variable "restricted_services" {
  type = list(string)
  default = [
    "healthcare.googleapis.com",
    "bigquery.googleapis.com",
    "storage.googleapis.com",
    "pubsub.googleapis.com",
    "dlp.googleapis.com",
    "cloudkms.googleapis.com",
    "aiplatform.googleapis.com",
  ]
}

# Corporate / trusted egress IPs allowed to reach perimeter-protected services.
variable "trusted_ip_ranges" {
  description = "CIDRs for the 'trusted' access level (office VPN, etc.)."
  type        = list(string)
  default     = ["203.0.113.0/24"] # placeholder — replace with real ranges
}

variable "vpn_config" {
  description = "Optional HA VPN per environment (keyed by short code). Empty = disabled."
  type = map(object({
    peer_gateway_ips = list(string)
    peer_asn         = number
    shared_secret    = string
    onprem_cidrs     = list(string)
  }))
  default = {}
}
