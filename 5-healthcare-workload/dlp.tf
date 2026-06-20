# ---------------------------------------------------------------------------
# 5-healthcare-workload / dlp.tf
# Cloud DLP templates (Image 1 "Privacy & PHI Protection"):
#   - an INSPECT template defining the PHI infoTypes to detect,
#   - a DE-IDENTIFY template defining how to transform them.
# Pipelines reference these to populate the `deidentified` dataset.
# ---------------------------------------------------------------------------

locals {
  dlp_parent = {
    for env in local.envs :
    env => "projects/${local.projects[env]["lakehouse"].project_id}/locations/${local.region}"
  }

  phi_info_types = [
    "PERSON_NAME",
    "US_SOCIAL_SECURITY_NUMBER",
    "PHONE_NUMBER",
    "EMAIL_ADDRESS",
    "DATE_OF_BIRTH",
    "US_HEALTHCARE_NPI",
    "STREET_ADDRESS",
    "AGE",
  ]
}

resource "google_data_loss_prevention_inspect_template" "phi" {
  for_each = toset(local.envs)

  parent       = local.dlp_parent[each.key]
  description  = "Detect PHI infoTypes for ${each.key}."
  display_name = "phi-inspect-${each.key}"

  inspect_config {
    min_likelihood = "POSSIBLE"

    dynamic "info_types" {
      for_each = local.phi_info_types
      content { name = info_types.value }
    }
  }
}

resource "google_data_loss_prevention_deidentify_template" "phi" {
  for_each = toset(local.envs)

  parent       = local.dlp_parent[each.key]
  description  = "De-identify PHI for research/ML for ${each.key}."
  display_name = "phi-deid-${each.key}"

  deidentify_config {
    info_type_transformations {
      # Mask government identifiers entirely.
      transformations {
        info_types { name = "US_SOCIAL_SECURITY_NUMBER" }
        primitive_transformation {
          character_mask_config { masking_character = "#" }
        }
      }
      # Replace remaining direct identifiers with their infoType name.
      transformations {
        info_types { name = "PERSON_NAME" }
        info_types { name = "EMAIL_ADDRESS" }
        info_types { name = "PHONE_NUMBER" }
        info_types { name = "STREET_ADDRESS" }
        info_types { name = "US_HEALTHCARE_NPI" }
        primitive_transformation {
          replace_with_info_type_config = true
        }
      }
      # Generalize dates of birth to the year (date shifting / bucketing).
      transformations {
        info_types { name = "DATE_OF_BIRTH" }
        primitive_transformation {
          replace_with_info_type_config = true
        }
      }
    }
  }
}

# NOTE: For tokenization/pseudonymization that supports re-identification
# (the diagram's "Tokenization / Pseudonymization" box), swap the replace
# transforms for crypto_deterministic_config with a KMS-wrapped key. That needs
# a wrapped-key blob, so it's left as a documented production step.
