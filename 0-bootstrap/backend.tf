# ---------------------------------------------------------------------------
# 0-bootstrap / backend.tf
# Bootstrap starts on LOCAL state. After the first `terraform apply` creates
# the state bucket, uncomment this block and run:
#     terraform init -migrate-state
# to move bootstrap's own state into the bucket it just created.
# ---------------------------------------------------------------------------

# terraform {
#   backend "gcs" {
#     bucket = "hcf-b-seed-tfstate"   # = output tfstate_bucket
#     prefix = "bootstrap"
#   }
# }
