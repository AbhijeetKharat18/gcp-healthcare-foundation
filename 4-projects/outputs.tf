# ---------------------------------------------------------------------------
# 4-projects / outputs.tf
# Nested map env_short -> component -> { project_id, project_number }.
# Stage 5 deploys workloads into these projects.
# ---------------------------------------------------------------------------

output "projects" {
  description = "All workload projects, grouped by environment then component."
  value = {
    for short in distinct(values(var.env_short_map)) :
    short => {
      for comp in keys(var.components) :
      comp => {
        project_id     = module.project["${short}-${comp}"].project_id
        project_number = module.project["${short}-${comp}"].project_number
      }
    }
  }
}
