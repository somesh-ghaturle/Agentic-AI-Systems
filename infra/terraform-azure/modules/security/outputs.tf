output "keyvault_id" {
  description = "Vault resource ID, for diagnostic settings and private endpoints."
  value       = azurerm_key_vault.kv.id
}

output "keyvault_uri" {
  description = "Vault URI. Workloads build Key Vault references from this."
  value       = azurerm_key_vault.kv.vault_uri
}

output "keyvault_name" {
  description = "Vault name, for alarm scoping and CLI use."
  value       = azurerm_key_vault.kv.name
}

output "model_key_secret_id" {
  description = "ID of the model API key secret when one was created; null otherwise."
  value       = one(azurerm_key_vault_secret.model_key[*].id)
}
