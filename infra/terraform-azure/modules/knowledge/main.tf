resource "azurerm_search_service" "knowledge" {
  name                = "${var.name_prefix}-search"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = var.sku

  # replica_count and partition_count must be 1 for Standard or Free in most default plans, or configurable
  replica_count   = 1
  partition_count = 1

  tags = var.tags
}
