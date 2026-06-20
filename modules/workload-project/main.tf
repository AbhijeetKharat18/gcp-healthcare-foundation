# ---------------------------------------------------------------------------
# modules/workload-project/main.tf
# One workload project: created in an env folder, attached to that env's
# Shared VPC as a SERVICE project, with its APIs enabled and subnet usage
# granted to the identities that build resources in it.
# ---------------------------------------------------------------------------

locals {
  project_id = "${var.prefix}-${var.env_short}-${var.component}"
}

resource "google_project" "this" {
  name            = local.project_id
  project_id      = local.project_id
  folder_id       = var.folder_id
  billing_account = var.billing_account
  deletion_policy = "PREVENT"

  labels = {
    environment = var.env_short
    component   = var.component
    managed-by  = "terraform"
  }
}

resource "google_project_service" "apis" {
  for_each = toset(var.apis)

  project            = google_project.this.project_id
  service            = each.value
  disable_on_destroy = false
}

# --- Attach as Shared VPC service project -----------------------------------
resource "google_compute_shared_vpc_service_project" "attach" {
  host_project    = var.host_project_id
  service_project = google_project.this.project_id

  depends_on = [google_project_service.apis]
}

# --- Subnet usage for this project's builder identities ----------------------
locals {
  network_user_members = [
    "serviceAccount:${google_project.this.number}-compute@developer.gserviceaccount.com",
    "serviceAccount:${google_project.this.number}@cloudservices.gserviceaccount.com",
  ]
}

resource "google_compute_subnetwork_iam_member" "network_user" {
  for_each = toset(local.network_user_members)

  project    = var.host_project_id
  region     = var.region
  subnetwork = var.subnet_name
  role       = "roles/compute.networkUser"
  member     = each.value

  depends_on = [google_compute_shared_vpc_service_project.attach]
}
