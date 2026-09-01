resource "azurerm_cosmosdb_account" "state" {
  count = var.enable_resources ? 1 : 0

  name                = "${var.name_prefix}-state"
  location            = var.location
  resource_group_name = var.resource_group_name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"

  consistency_policy {
    consistency_level = "Session"
  }

  geo_location {
    location          = var.location
    failover_priority = 0
  }
}

resource "azurerm_cosmosdb_sql_database" "state" {
  count               = var.enable_resources ? 1 : 0
  name                = "agent-state"
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.state[0].name
  throughput          = 400
}
