resource "azurerm_logic_app_workflow" "orchestrator" {
  name                = "${var.name_prefix}-orchestrator"
  location            = var.location
  resource_group_name = var.resource_group_name

  tags = var.tags
}
