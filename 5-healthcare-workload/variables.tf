# 5-healthcare-workload / variables.tf
variable "bootstrap_state_bucket" {
  type = string
}

variable "analysts_group" {
  description = "Group granted fine-grained read on low-sensitivity PHI columns."
  type        = string
  default     = "data-analysts@example.com"
}

variable "create_example_views" {
  description = "Create the example RLS view (needs curated tables to exist)."
  type        = bool
  default     = false
}
