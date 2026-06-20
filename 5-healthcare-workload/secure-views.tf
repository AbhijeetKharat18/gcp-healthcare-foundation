# ---------------------------------------------------------------------------
# 5-healthcare-workload / secure-views.tf
# The `secure_views` dataset (created in lakehouse.tf) exposes governed access
# to curated_phi. We authorize it to read curated_phi at the dataset level, so
# its views work regardless of which curated tables exist yet. An optional
# example view shows the row-level-security (RLS) pattern using SESSION_USER().
# ---------------------------------------------------------------------------

# Authorize all VIEWS in secure_views to read curated_phi (authorized dataset).
resource "google_bigquery_dataset_access" "secure_views_read_curated" {
  for_each = toset(local.envs)

  project    = local.projects[each.key]["lakehouse"].project_id
  dataset_id = google_bigquery_dataset.medallion["${each.key}-curated_phi"].dataset_id

  dataset {
    dataset {
      project_id = local.projects[each.key]["lakehouse"].project_id
      dataset_id = google_bigquery_dataset.medallion["${each.key}-secure_views"].dataset_id
    }
    target_types = ["VIEWS"]
  }
}

# Optional example authorized view demonstrating RLS. Off by default because it
# references curated tables that don't exist in a fresh greenfield deployment.
resource "google_bigquery_table" "example_rls_view" {
  for_each = var.create_example_views ? toset(local.envs) : toset([])

  project             = local.projects[each.key]["lakehouse"].project_id
  dataset_id          = google_bigquery_dataset.medallion["${each.key}-secure_views"].dataset_id
  table_id            = "v_encounter_secured"
  deletion_protection = false

  view {
    use_legacy_sql = false
    # Row-level security: a user only sees rows for facilities they're mapped to.
    query = <<-SQL
      SELECT e.*
      FROM `${local.projects[each.key]["lakehouse"].project_id}.curated_phi.encounter` AS e
      WHERE e.facility_id IN (
        SELECT facility_id
        FROM `${local.projects[each.key]["lakehouse"].project_id}.secure_views.user_facility_map`
        WHERE user_email = SESSION_USER()
      )
    SQL
  }
}
