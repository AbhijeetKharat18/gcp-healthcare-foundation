# ---------------------------------------------------------------------------
# 4-projects / variables.tf
# The component catalog: which workload projects exist per environment and
# which APIs each enables. These map to the diagram's columns:
#   ingestion       -> Secure Ingestion Layer (GKE MLLP adapter, Pub/Sub, GCS)
#   healthcare-core -> Cloud Healthcare API stores (FHIR / HL7v2 / DICOM)
#   lakehouse       -> BigQuery medallion datasets + DLP de-id
#   delivery        -> Cloud Run / API Gateway / Vertex / Looker hooks
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

variable "components" {
  description = "Workload component -> APIs to enable."
  type        = map(list(string))
  default = {
    ingestion = [
      "compute.googleapis.com",
      "container.googleapis.com",
      "pubsub.googleapis.com",
      "storage.googleapis.com",
      "dataflow.googleapis.com",
      "dns.googleapis.com",
      "cloudkms.googleapis.com",
    ]
    healthcare-core = [
      "healthcare.googleapis.com",
      "pubsub.googleapis.com",
      "storage.googleapis.com",
      "cloudkms.googleapis.com",
    ]
    lakehouse = [
      "bigquery.googleapis.com",
      "bigquerydatatransfer.googleapis.com",
      "storage.googleapis.com",
      "dlp.googleapis.com",
      "datacatalog.googleapis.com",
      "cloudkms.googleapis.com",
    ]
    delivery = [
      "run.googleapis.com",
      "apigateway.googleapis.com",
      "aiplatform.googleapis.com",
      "bigquery.googleapis.com",
      "compute.googleapis.com",
    ]
  }
}
