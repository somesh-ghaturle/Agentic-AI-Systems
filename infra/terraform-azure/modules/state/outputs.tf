output "table_name" {
  description = "Name of the execution-state table."
  value       = azurerm_cosmosdb_table.execution_state.name
}

output "account_name" {
  description = "Name of the Cosmos DB account that holds execution state."
  value       = azurerm_cosmosdb_account.state.name
}

output "table_endpoint" {
  description = "Table endpoint to hand to `azure-data-tables`. Derived from the account name because the account's own `endpoint` attribute is the document endpoint, which the Table client does not accept."
  value       = "https://${azurerm_cosmosdb_account.state.name}.table.cosmos.azure.com:443/"
}

output "account_id" {
  description = "Resource ID of the account, for role assignments and diagnostic settings."
  value       = azurerm_cosmosdb_account.state.id
}
