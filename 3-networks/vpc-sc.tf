# ---------------------------------------------------------------------------
# 3-networks / vpc-sc.tf
# VPC Service Controls: the dotted "perimeter" boundary in both diagrams.
# We create one org access policy, a "trusted" access level, and one REGULAR
# service perimeter PER environment. Perimeters start with no member projects;
# stage 4 adds each workload project as it is created (see note below).
# ---------------------------------------------------------------------------

resource "google_access_context_manager_access_policy" "org" {
  parent = "organizations/${local.org_id}"
  title  = "hcf-org-access-policy"
}

# Trusted network access level (corporate egress IPs).
resource "google_access_context_manager_access_level" "trusted" {
  parent = "accessPolicies/${google_access_context_manager_access_policy.org.name}"
  name   = "accessPolicies/${google_access_context_manager_access_policy.org.name}/accessLevels/trusted"
  title  = "trusted"

  basic {
    conditions {
      ip_subnetworks = var.trusted_ip_ranges
    }
  }
}

# One perimeter per environment.
resource "google_access_context_manager_service_perimeter" "env" {
  for_each = var.env_short_map

  parent = "accessPolicies/${google_access_context_manager_access_policy.org.name}"
  name   = "accessPolicies/${google_access_context_manager_access_policy.org.name}/servicePerimeters/sp_${each.value}"
  title  = "sp-${each.value}"

  status {
    restricted_services = var.restricted_services
    access_levels       = [google_access_context_manager_access_level.trusted.name]

    # Projects are added in stage 4 via a dedicated resource; keep empty here.
    resources = []

    vpc_accessible_services {
      enable_restriction = true
      allowed_services   = ["RESTRICTED-SERVICES"]
    }
  }

  # Let stage 4 manage perimeter membership without Terraform fighting it.
  lifecycle {
    ignore_changes = [status[0].resources]
  }
}
