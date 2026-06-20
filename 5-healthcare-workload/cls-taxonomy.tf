# ---------------------------------------------------------------------------
# 5-healthcare-workload / cls-taxonomy.tf
# Column-Level Security: a Data Catalog policy-tag taxonomy per environment.
# Columns in the lakehouse are tagged (in their schema policyTags) with one of
# these tags; only principals granted fineGrainedReader on a tag can read the
# columns carrying it. Maps to "Column-Level Security (CLS)" in both diagrams.
# ---------------------------------------------------------------------------

resource "google_data_catalog_taxonomy" "phi" {
  for_each = toset(local.envs)

  project                = local.projects[each.key]["lakehouse"].project_id
  region                 = local.region
  display_name           = "phi-classification-${each.key}"
  description            = "PHI sensitivity classification for column-level security."
  activated_policy_types = ["FINE_GRAINED_ACCESS_CONTROL"]
}

# Sensitivity levels (high = direct identifiers, low = quasi-identifiers).
locals {
  sensitivity_levels = {
    phi_high   = "Direct identifiers (name, SSN, MRN, contact)."
    phi_medium = "Quasi-identifiers (DOB, ZIP, dates)."
    phi_low    = "Low-sensitivity clinical attributes."
  }

  env_tags = merge([
    for env in local.envs : {
      for level, desc in local.sensitivity_levels :
      "${env}-${level}" => { env = env, level = level, desc = desc }
    }
  ]...)
}

resource "google_data_catalog_policy_tag" "level" {
  for_each = local.env_tags

  taxonomy     = google_data_catalog_taxonomy.phi[each.value.env].id
  display_name = each.value.level
  description  = each.value.desc
}

# Example CLS grant: analysts may read low-sensitivity columns only.
resource "google_data_catalog_policy_tag_iam_member" "analysts_low" {
  for_each = toset(local.envs)

  policy_tag = google_data_catalog_policy_tag.level["${each.key}-phi_low"].id
  role       = "roles/datacatalog.categoryFineGrainedReader"
  member     = "group:${var.analysts_group}"
}
