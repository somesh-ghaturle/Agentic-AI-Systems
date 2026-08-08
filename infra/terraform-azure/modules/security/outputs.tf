output "keyvault_id" {
  value = azurerm_key_vault.kv.id
}

output "keyvault_uri" {
  value = azurerm_key_vault.kv.vault_uri
}

output "model_key_secret_id" {
  value       = length(azurerm_key_vault_secret.model_key) > 0 ? azurerm_key_vault_secret.model_key[0].id : null
  description = "ID of the model API key secret when created; null otherwise."
}
