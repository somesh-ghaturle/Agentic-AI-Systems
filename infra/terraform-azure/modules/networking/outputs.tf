output "resource_group_name" {
  value = azurerm_resource_group.rg.name
}

output "subnet_id" {
  value = azurerm_subnet.subnet.id
}

output "integration_subnet_id" {
  description = "The delegated subnet. Pass to the Function App modules as virtual_network_subnet_id — and only on a plan that supports it, which Y1 does not."
  value       = azurerm_subnet.integration.id
}
