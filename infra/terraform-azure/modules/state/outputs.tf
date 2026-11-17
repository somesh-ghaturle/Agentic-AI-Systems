output "endpoint" {
  description = "Document endpoint of the execution-state account."
  value       = azurerm_cosmosdb_account.state.endpoint
}

output "database_name" {
  description = "Name of the database that holds execution state."
  value       = azurerm_cosmosdb_sql_database.state.name
}

output "container_name" {
  description = "Name of the execution-state container. Partitioned by /execution_id."
  value       = azurerm_cosmosdb_sql_container.execution_state.name
}

output "account_name" {
  description = "Name of the Cosmos DB account that holds execution state."
  value       = azurerm_cosmosdb_account.state.name
}

output "account_id" {
  description = "Resource ID of the account, for the data-plane role assignment a tool needs before it can read or write state."
  value       = azurerm_cosmosdb_account.state.id
}
