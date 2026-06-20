# 2-environments / variables.tf
variable "bootstrap_state_bucket" {
  description = "GCS bucket holding 0-bootstrap + 1-org state."
  type        = string
}

# Short codes used in project IDs (long env names won't fit project-id limits).
variable "env_short_map" {
  description = "Full environment name -> short code."
  type        = map(string)
  default = {
    development   = "dev"
    nonproduction = "nonprod"
    production    = "prod"
  }
}

variable "budget_amounts" {
  description = "Monthly USD budget per environment (by short code)."
  type        = map(number)
  default = {
    dev     = 1000
    nonprod = 2000
    prod    = 5000
  }
}
