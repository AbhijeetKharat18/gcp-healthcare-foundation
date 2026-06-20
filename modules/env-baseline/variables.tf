# modules/env-baseline/variables.tf
variable "prefix"          { type = string }
variable "env"             { type = string } # full name, e.g. development
variable "env_short"       { type = string } # short code, e.g. dev
variable "folder_id"       { type = string } # numeric folder id (no folders/ prefix)
variable "billing_account" { type = string }
variable "region"          { type = string }

variable "budget_amount" {
  type    = number
  default = 1000
}

variable "labels" {
  type    = map(string)
  default = { managed-by = "terraform" }
}
