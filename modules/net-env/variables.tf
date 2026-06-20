# modules/net-env/variables.tf
variable "prefix"          { type = string }
variable "env_short"       { type = string }
variable "folder_id"       { type = string }
variable "billing_account" { type = string }
variable "region"          { type = string }

variable "cidr" {
  description = "CIDR plan for this environment."
  type = object({
    primary  = string
    pods     = string
    services = string
  })
}

variable "onprem_cidrs" {
  description = "On-prem/peer CIDRs reachable via VPN (allowed through firewall)."
  type        = list(string)
  default     = []
}
