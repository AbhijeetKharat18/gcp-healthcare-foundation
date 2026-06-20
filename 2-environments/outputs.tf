# 2-environments / outputs.tf
# env short code -> { base project, kms key } for stages 3-5.
output "environments" {
  description = "Per-environment baseline outputs keyed by short code."
  value = {
    for env, m in module.env :
    var.env_short_map[env] => {
      base_project_id = m.base_project_id
      kms_key_id      = m.kms_key_id
      kms_keyring_id  = m.kms_keyring_id
    }
  }
}
