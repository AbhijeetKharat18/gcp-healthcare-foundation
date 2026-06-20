# ---------------------------------------------------------------------------
# modules/net-env/firewall.tf
# Default-deny ingress is implicit. We add the minimum allow rules plus an
# explicit deny-all egress with narrow allows (egress lockdown for PHI).
# ---------------------------------------------------------------------------

# Allow internal traffic within the VPC (all defined ranges).
resource "google_compute_firewall" "allow_internal" {
  project   = google_project.host.project_id
  name      = "fw-${var.env_short}-allow-internal"
  network   = google_compute_network.vpc.name
  direction = "INGRESS"
  priority  = 1000

  source_ranges = [var.cidr.primary, var.cidr.pods, var.cidr.services]

  allow { protocol = "tcp" }
  allow { protocol = "udp" }
  allow { protocol = "icmp" }
}

# Allow IAP TCP forwarding (admin access without public IPs).
resource "google_compute_firewall" "allow_iap" {
  project       = google_project.host.project_id
  name          = "fw-${var.env_short}-allow-iap"
  network       = google_compute_network.vpc.name
  direction     = "INGRESS"
  priority      = 1000
  source_ranges = ["35.235.240.0/20"] # Google IAP range

  allow {
    protocol = "tcp"
    ports    = ["22", "3389", "443"]
  }
}

# Allow Google health checks (load balancers).
resource "google_compute_firewall" "allow_health_checks" {
  project       = google_project.host.project_id
  name          = "fw-${var.env_short}-allow-hc"
  network       = google_compute_network.vpc.name
  direction     = "INGRESS"
  priority      = 1000
  source_ranges = ["130.211.0.0/22", "35.191.0.0/16"]

  allow { protocol = "tcp" }
}

# --- Egress lockdown --------------------------------------------------------
# Allow egress only to internal ranges and the restricted Google APIs VIP;
# deny everything else. This keeps PHI workloads from talking to the internet.
resource "google_compute_firewall" "allow_egress_internal" {
  project            = google_project.host.project_id
  name               = "fw-${var.env_short}-egress-internal"
  network            = google_compute_network.vpc.name
  direction          = "EGRESS"
  priority           = 1000
  destination_ranges = [var.cidr.primary, var.cidr.pods, var.cidr.services]
  allow { protocol = "all" }
}

resource "google_compute_firewall" "allow_egress_restricted_apis" {
  project            = google_project.host.project_id
  name               = "fw-${var.env_short}-egress-gapis"
  network            = google_compute_network.vpc.name
  direction          = "EGRESS"
  priority           = 1000
  destination_ranges = [local.restricted_vip]
  allow {
    protocol = "tcp"
    ports    = ["443"]
  }
}

resource "google_compute_firewall" "deny_egress_all" {
  project            = google_project.host.project_id
  name               = "fw-${var.env_short}-egress-deny-all"
  network            = google_compute_network.vpc.name
  direction          = "EGRESS"
  priority           = 65534
  destination_ranges = ["0.0.0.0/0"]
  deny { protocol = "all" }
}

# --- On-prem (VPN) connectivity: allow only when CIDRs are provided ----------
resource "google_compute_firewall" "allow_ingress_onprem" {
  for_each = length(var.onprem_cidrs) > 0 ? toset(["enabled"]) : toset([])

  project       = google_project.host.project_id
  name          = "fw-${var.env_short}-ingress-onprem"
  network       = google_compute_network.vpc.name
  direction     = "INGRESS"
  priority      = 1000
  source_ranges = var.onprem_cidrs
  allow { protocol = "tcp" }
  allow { protocol = "udp" }
  allow { protocol = "icmp" }
}

resource "google_compute_firewall" "allow_egress_onprem" {
  for_each = length(var.onprem_cidrs) > 0 ? toset(["enabled"]) : toset([])

  project            = google_project.host.project_id
  name               = "fw-${var.env_short}-egress-onprem"
  network            = google_compute_network.vpc.name
  direction          = "EGRESS"
  priority           = 1000
  destination_ranges = var.onprem_cidrs
  allow { protocol = "all" }
}
