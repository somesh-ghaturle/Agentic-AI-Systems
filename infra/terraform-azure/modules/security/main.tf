# Security module: placeholder for keyvault, policies, and diagnostics
resource "azurerm_key_vault" "kv" {
  name                        = "${var.name_prefix}-kv"
  location                    = var.location
  resource_group_name         = var.resource_group_name
  tenant_id                   = var.tenant_id
  sku_name                    = "standard"
  soft_delete_enabled         = true
  purge_protection_enabled    = false
}

# Grant access to a service principal when provided
resource "azurerm_key_vault_access_policy" "sp_policy" {
  count               = var.service_principal_object_id == "" ? 0 : 1
  key_vault_id        = azurerm_key_vault.kv.id
  tenant_id           = var.tenant_id
  object_id           = var.service_principal_object_id

  secret_permissions = ["get", "list", "set", "delete"]
}

# Optional: create a Key Vault secret to hold a model API key (value passed in securely)
resource "azurerm_key_vault_secret" "model_key" {
  count                = var.create_model_key_secret ? 1 : 0
  name                 = var.model_key_secret_name
  value                = var.model_key_secret_value
  key_vault_id         = azurerm_key_vault.kv.id
}
