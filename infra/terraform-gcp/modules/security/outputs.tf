output "kms_key_id" {
  description = "Full resource ID of the crypto key, for `kms_key_name` arguments elsewhere."
  value       = google_kms_crypto_key.main.id
}

output "kms_key_ring_id" {
  description = "Key ring resource ID."
  value       = google_kms_key_ring.main.id
}

output "model_key_secret_id" {
  description = "Secret Manager secret ID for the model API key, or null when not created."
  value       = var.create_model_key_secret ? google_secret_manager_secret.model_key[0].secret_id : null
}
