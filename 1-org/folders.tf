# ---------------------------------------------------------------------------
# 1-org / folders.tf
# Folder hierarchy:
#   org
#   ├── fldr-common          (shared/centralized: logging, security, networking host)
#   ├── fldr-development
#   ├── fldr-nonproduction
#   └── fldr-production
#
# Stage 4 creates the actual workload projects inside these env folders.
# ---------------------------------------------------------------------------

resource "google_folder" "common" {
  display_name = "fldr-common"
  parent       = "organizations/${local.org_id}"
}

resource "google_folder" "environments" {
  for_each = toset(var.environments)

  display_name = "fldr-${each.value}"
  parent       = "organizations/${local.org_id}"
}
