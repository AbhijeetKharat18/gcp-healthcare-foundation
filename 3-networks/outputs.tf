# ---------------------------------------------------------------------------
# 3-networks / outputs.tf
# Consumed by stage 4 (attach service projects, add to perimeter) and stage 5.
# ---------------------------------------------------------------------------

output "networks" {
  description = "Per-env network info keyed by short code."
  value = {
    for env, m in module.net :
    var.env_short_map[env] => {
      host_project_id = m.host_project_id
      network_id      = m.network_id
      network_name    = m.network_name
      subnet_id       = m.subnet_id
      subnet_name     = m.subnet_name
    }
  }
}

output "access_policy_name" {
  description = "VPC-SC access policy name (accessPolicies/NNN)."
  value       = google_access_context_manager_access_policy.org.name
}

output "perimeter_names" {
  description = "Per-env perimeter resource names, keyed by short code."
  value = {
    for k, p in google_access_context_manager_service_perimeter.env :
    k => p.name
  }
}
