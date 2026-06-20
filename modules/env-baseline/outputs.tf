# modules/env-baseline/outputs.tf
output "base_project_id" { value = google_project.base.project_id }
output "kms_keyring_id"   { value = google_kms_key_ring.env.id }
output "kms_key_id"       { value = google_kms_crypto_key.env.id }
