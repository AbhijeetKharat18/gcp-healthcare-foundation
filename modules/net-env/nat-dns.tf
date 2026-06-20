# ---------------------------------------------------------------------------
# modules/net-env/nat-dns.tf
# Cloud NAT for controlled egress (VMs have no external IPs per org policy),
# and a private DNS zone that points *.googleapis.com at the restricted VIP so
# Google API calls stay on Google's backbone and inside the VPC-SC perimeter.
# ---------------------------------------------------------------------------

resource "google_compute_router" "router" {
  project = google_project.host.project_id
  name    = "rtr-${var.env_short}"
  region  = var.region
  network = google_compute_network.vpc.id
}

resource "google_compute_router_nat" "nat" {
  project                            = google_project.host.project_id
  name                               = "nat-${var.env_short}"
  router                             = google_compute_router.router.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# --- Private DNS for restricted.googleapis.com ------------------------------
resource "google_dns_managed_zone" "googleapis" {
  project     = google_project.host.project_id
  name        = "dz-${var.env_short}-googleapis"
  dns_name    = "googleapis.com."
  description = "Route Google APIs via restricted VIP (VPC-SC)."
  visibility  = "private"

  private_visibility_config {
    networks {
      network_url = google_compute_network.vpc.id
    }
  }
}

resource "google_dns_record_set" "restricted_a" {
  project      = google_project.host.project_id
  managed_zone = google_dns_managed_zone.googleapis.name
  name         = "restricted.googleapis.com."
  type         = "A"
  ttl          = 300
  rrdatas      = ["199.36.153.4", "199.36.153.5", "199.36.153.6", "199.36.153.7"]
}

resource "google_dns_record_set" "wildcard_cname" {
  project      = google_project.host.project_id
  managed_zone = google_dns_managed_zone.googleapis.name
  name         = "*.googleapis.com."
  type         = "CNAME"
  ttl          = 300
  rrdatas      = ["restricted.googleapis.com."]
}
