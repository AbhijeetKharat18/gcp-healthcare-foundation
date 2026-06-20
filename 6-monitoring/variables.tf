# 6-monitoring / variables.tf
variable "bootstrap_state_bucket" {
  type = string
}

variable "alert_email" {
  description = "Email address for security + ops alert notifications."
  type        = string
  default     = "alerts@example.com"
}
