resource "azurerm_storage_account" "state_sa" {
  name                     = replace("${var.name_prefix}statesa", "-", "")
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = var.account_replication_type

  tags = var.tags
}

resource "azurerm_storage_table" "execution_state" {
  name               = "executionstate"
  storage_account_id = azurerm_storage_account.state_sa.id
}
