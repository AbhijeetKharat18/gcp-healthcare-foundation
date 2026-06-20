# ---------------------------------------------------------------------------
# 6-monitoring / main.tf
# Per-environment operational monitoring scope + dashboard.
# ---------------------------------------------------------------------------

module "monitoring" {
  source   = "../modules/monitoring-env"
  for_each = toset(local.envs)

  env_short          = each.key
  scoping_project_id = local.envs_meta[each.key].base_project_id

  # All workload projects in this environment become monitored projects.
  monitored_project_ids = [
    for comp, p in local.projects[each.key] : p.project_id
  ]

  alert_email = var.alert_email
}
