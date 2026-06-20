# ---------------------------------------------------------------------------
# modules/env-baseline/main.tf
# Per-environment shared baseline: a small "base" project that holds the
# environment's CMEK keyring/key, plus a billing budget scoped to that env.
# Stages 3-5 reference the env key for encrypting workload data.
# ---------------------------------------------------------------------------

locals {
  base_project_id = "${var.prefix}-${var.env_short}-base"
}

resource "google_project" "base" {
  name            = local.base_project_id
  project_id      = local.base_project_id
  folder_id       = var.folder_id
  billing_account = var.billing_account
  deletion_policy = "PREVENT"

  labels = merge(var.labels, {
    environment = var.env_short
    component   = "env-baseline"
  })
}

resource "google_project_service" "base" {
  for_each = toset([
    "cloudkms.googleapis.com",
    "monitoring.googleapis.com",
    "billingbudgets.googleapis.com",
    "secretmanager.googleapis.com",
  ])
  project            = google_project.base.project_id
  service            = each.value
  disable_on_destroy = false
}

# --- Environment CMEK keyring + default key ---------------------------------
resource "google_kms_key_ring" "env" {
  project    = google_project.base.project_id
  name       = "${var.prefix}-${var.env_short}-keyring"
  location   = var.region
  depends_on = [google_project_service.base]
}

resource "google_kms_crypto_key" "env" {
  name            = "${var.prefix}-${var.env_short}-key"
  key_ring        = google_kms_key_ring.env.id
  rotation_period = "7776000s" # 90 days

  labels = { environment = var.env_short }
}

# --- Per-environment billing budget with threshold alerts -------------------
# Scoped by the `environment` label that stage-4 projects carry.
resource "google_billing_budget" "env" {
  billing_account = var.billing_account
  display_name    = "budget-${var.env_short}"

  budget_filter {
    labels = {
      environment = var.env_short
    }
  }

  amount {
    specified_amount {
      currency_code = "USD"
      units         = tostring(var.budget_amount)
    }
  }

  dynamic "threshold_rules" {
    for_each = [0.5, 0.75, 0.9, 1.0]
    content {
      threshold_percent = threshold_rules.value
    }
  }

  depends_on = [google_project_service.base]
}
