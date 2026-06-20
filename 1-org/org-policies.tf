# ---------------------------------------------------------------------------
# 1-org / org-policies.tf
# Organization-wide guardrails (Org Policy v2). These are "compliance by
# design": they constrain the whole org regardless of what teams deploy later.
# Maps to the Governance & Org Policies band in both architecture diagrams.
# ---------------------------------------------------------------------------

# --- Boolean (enforced) constraints -----------------------------------------
locals {
  boolean_enforced_policies = [
    "iam.disableServiceAccountKeyCreation", # no long-lived SA keys
    "iam.disableServiceAccountKeyUpload",
    "compute.skipDefaultNetworkCreation", # no auto default VPC
    "compute.requireOsLogin",
    "sql.restrictPublicIp", # Cloud SQL: no public IP
    "storage.uniformBucketLevelAccess",
    "compute.disableSerialPortAccess",
  ]
}

resource "google_org_policy_policy" "boolean_enforced" {
  for_each = toset(local.boolean_enforced_policies)

  name   = "organizations/${local.org_id}/policies/${each.value}"
  parent = "organizations/${local.org_id}"

  spec {
    rules {
      enforce = "TRUE"
    }
  }
}

# --- Resource location restriction (data residency for PHI) -----------------
resource "google_org_policy_policy" "resource_locations" {
  name   = "organizations/${local.org_id}/policies/gcp.resourceLocations"
  parent = "organizations/${local.org_id}"

  spec {
    rules {
      values {
        allowed_values = var.allowed_locations
      }
    }
  }
}

# --- CMEK required for sensitive services -----------------------------------
resource "google_org_policy_policy" "require_cmek" {
  name   = "organizations/${local.org_id}/policies/gcp.restrictNonCmekServices"
  parent = "organizations/${local.org_id}"

  spec {
    rules {
      values {
        denied_values = var.cmek_required_services
      }
    }
  }
}

# --- Deny external IPs on VMs -----------------------------------------------
resource "google_org_policy_policy" "deny_vm_external_ip" {
  name   = "organizations/${local.org_id}/policies/compute.vmExternalIpAccess"
  parent = "organizations/${local.org_id}"

  spec {
    rules {
      deny_all = "TRUE"
    }
  }
}
