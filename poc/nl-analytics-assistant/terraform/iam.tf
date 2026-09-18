# poc/nl-analytics-assistant/terraform/iam.tf
# The delivery SA already reads the secure_views dataset (granted in
# 5-healthcare-workload/iam.tf). This POC adds only the two capabilities it is
# still missing, keeping least privilege:
#   - call Vertex AI (Gemini) in the delivery project, and
#   - run BigQuery query jobs in the lakehouse project (it can already read the
#     data; jobUser lets it execute the SELECT).
# It gains NO new data-read scope, so it still cannot touch raw/standardized/
# curated PHI.

resource "google_project_iam_member" "delivery_vertex_user" {
  project = local.delivery_project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${local.delivery_sa}"
}

resource "google_project_iam_member" "delivery_bq_job_user" {
  project = local.lakehouse_project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${local.delivery_sa}"
}

# The Terraform SA must be able to deploy Cloud Run "as" the delivery runtime SA.
resource "google_service_account_iam_member" "tf_can_actas_delivery" {
  service_account_id = "projects/${local.delivery_project_id}/serviceAccounts/${local.delivery_sa}"
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${local.tf_sa}"
}
