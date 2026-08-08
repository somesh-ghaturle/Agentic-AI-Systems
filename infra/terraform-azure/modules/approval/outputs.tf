output "servicebus_namespace_name" {
  value = azurerm_servicebus_namespace.sb.name
}

output "servicebus_topic_name" {
  value = azurerm_servicebus_topic.approval.name
}

output "servicebus_topic_id" {
  value = azurerm_servicebus_topic.approval.id
}
