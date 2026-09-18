# poc/nl-analytics-assistant/terraform/main.tf
# The Cloud Run service for the NL Analytics Assistant. Runs in the delivery
# project as sa-delivery, with internal-only ingress so it stays reachable only
# from inside the VPC-SC perimeter (front it with an internal LB / IAP for users).

resource "google_cloud_run_v2_service" "assistant" {
  name     = "${local.prefix}-${var.target_env}-nl-analytics"
  project  = local.delivery_project_id
  location = local.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_ONLY"

  deletion_protection = false

  template {
    service_account = local.delivery_sa

    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }

    containers {
      image = var.container_image

      ports {
        container_port = 8080
      }

      # Production path: Gemini on Vertex + BigQuery over secure_views.
      env {
        name  = "NLA_PROVIDER"
        value = "vertex"
      }
      env {
        name  = "NLA_EXECUTOR"
        value = "bigquery"
      }
      # BigQuery jobs run in (and read secure_views from) the lakehouse project.
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = local.lakehouse_project_id
      }
      env {
        name  = "NLA_BQ_DATASET"
        value = "secure_views"
      }
      env {
        name  = "NLA_BQ_LOCATION"
        value = local.region
      }
      # Vertex AI runs in the delivery project (in-perimeter).
      env {
        name  = "NLA_VERTEX_PROJECT"
        value = local.delivery_project_id
      }
      env {
        name  = "NLA_VERTEX_LOCATION"
        value = var.vertex_location
      }
      env {
        name  = "NLA_VERTEX_MODEL"
        value = var.vertex_model
      }
      env {
        name  = "NLA_MAX_ROWS"
        value = tostring(var.max_rows)
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }
  }

  depends_on = [
    google_project_iam_member.delivery_vertex_user,
    google_project_iam_member.delivery_bq_job_user,
    google_service_account_iam_member.tf_can_actas_delivery,
  ]
}

# Authenticated invokers only (no allUsers). Front with IAP / internal LB.
resource "google_cloud_run_v2_service_iam_member" "invokers" {
  for_each = toset(var.invoker_members)

  project  = google_cloud_run_v2_service.assistant.project
  location = google_cloud_run_v2_service.assistant.location
  name     = google_cloud_run_v2_service.assistant.name
  role     = "roles/run.invoker"
  member   = each.value
}
