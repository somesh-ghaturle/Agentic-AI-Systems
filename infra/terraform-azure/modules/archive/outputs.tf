output "container_name" {
  value = azurerm_storage_container.archive.name
}

output "storage_account_name" {
  value = azurerm_storage_account.archive_sa.name
}
