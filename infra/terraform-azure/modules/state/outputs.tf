output "table_name" {
  value = azurerm_storage_table.execution_state.name
}

output "storage_account_name" {
  value = azurerm_storage_account.state_sa.name
}
