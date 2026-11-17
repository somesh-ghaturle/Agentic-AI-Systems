output "storage_account_name" {
  description = "Storage account name for each environment's backend block."
  value       = azurerm_storage_account.state.name
}

output "backend_block" {
  description = "The backend block to paste into an environment root in place of `backend \"local\" {}`, with `<env>` replaced."
  value       = <<-EOT
    backend "azurerm" {
      resource_group_name  = "${azurerm_resource_group.state.name}"
      storage_account_name = "${azurerm_storage_account.state.name}"
      container_name       = "${azurerm_storage_container.state.name}"
      key                  = "agentic/<env>.tfstate"
      use_azuread_auth     = true
    }
  EOT
}
