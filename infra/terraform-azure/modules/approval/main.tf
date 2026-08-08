resource "azurerm_servicebus_namespace" "sb" {
  name                = "${var.name_prefix}-sb-namespace"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "Standard"

  tags = var.tags
}

resource "azurerm_servicebus_topic" "approval" {
  name         = "approval-requests"
  namespace_id = azurerm_servicebus_namespace.sb.id
}

resource "azurerm_servicebus_subscription" "approval_sub" {
  name               = "approval-sub"
  topic_id           = azurerm_servicebus_topic.approval.id
  max_delivery_count = 10
}
