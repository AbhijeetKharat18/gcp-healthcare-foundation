# poc/nl-analytics-assistant/terraform/variables.tf

variable "bootstrap_state_bucket" {
  description = "GCS bucket holding the foundation's Terraform state (0-bootstrap output)."
  type        = string
}

variable "target_env" {
  description = "Which environment to deploy the POC into (env_short: dev/nonprod/prod)."
  type        = string
  default     = "dev"
}

variable "container_image" {
  description = "Fully-qualified container image for the assistant (e.g. REGION-docker.pkg.dev/PROJECT/REPO/nl-analytics:TAG)."
  type        = string
}

variable "vertex_location" {
  description = "Vertex AI location for Gemini calls."
  type        = string
  default     = "us-central1"
}

variable "vertex_model" {
  description = "Gemini model used for text-to-SQL."
  type        = string
  default     = "gemini-2.5-pro"
}

variable "max_rows" {
  description = "Maximum rows the assistant will return from any query."
  type        = number
  default     = 1000
}

variable "invoker_members" {
  description = "IAM members allowed to invoke the service (e.g. [\"group:analysts@example.com\"])."
  type        = list(string)
  default     = []
}
