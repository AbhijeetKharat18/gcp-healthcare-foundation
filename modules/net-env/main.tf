# ---------------------------------------------------------------------------
# modules/net-env/main.tf
# Per-environment network: a Shared VPC HOST project with one custom-mode VPC,
# a primary subnet (Private Google Access on) with secondary ranges for GKE,
# Cloud NAT for controlled egress, baseline firewall, and private DNS for the
# restricted.googleapis.com VIP (the backbone for VPC-SC private connectivity).
# Service projects are ATTACHED in stage 4 once they exist.
# ---------------------------------------------------------------------------

locals {
  host_project_id = "${var.prefix}-${var.env_short}-net"
  network_name    = "vpc-${var.env_short}-shared"
  subnet_name     = "sn-${var.env_short}-${var.region}"
  restricted_vip  = "199.36.153.4/30" # restricted.googleapis.com VIP block
}

# --- Shared VPC host project ------------------------------------------------
resource "google_project" "host" {
  name            = local.host_project_id
  project_id      = local.host_project_id
  folder_id       = var.folder_id
  billing_account = var.billing_account
  deletion_policy = "PREVENT"
  labels          = { environment = var.env_short, component = "network-host" }
}

resource "google_project_service" "host" {
  for_each = toset([
    "compute.googleapis.com",
    "dns.googleapis.com",
    "servicenetworking.googleapis.com",
  ])
  project            = google_project.host.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_compute_shared_vpc_host_project" "host" {
  project    = google_project.host.project_id
  depends_on = [google_project_service.host]
}

# --- VPC + subnet -----------------------------------------------------------
resource "google_compute_network" "vpc" {
  project                 = google_project.host.project_id
  name                    = local.network_name
  auto_create_subnetworks = false
  routing_mode            = "GLOBAL"
  depends_on              = [google_project_service.host]
}

resource "google_compute_subnetwork" "primary" {
  project       = google_project.host.project_id
  name          = local.subnet_name
  region        = var.region
  network       = google_compute_network.vpc.id
  ip_cidr_range = var.cidr.primary

  # Required for private workloads to reach Google APIs without external IPs.
  private_ip_google_access = true

  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = var.cidr.pods
  }
  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = var.cidr.services
  }

  log_config {
    aggregation_interval = "INTERVAL_5_SEC"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}
