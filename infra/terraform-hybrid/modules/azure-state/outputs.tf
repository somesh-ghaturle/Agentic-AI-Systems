output "state_endpoint" {
  description = "Cosmos DB endpoint, or null while resources are disabled."
  value       = try(azurerm_cosmosdb_account.state[0].endpoint, null)
}
