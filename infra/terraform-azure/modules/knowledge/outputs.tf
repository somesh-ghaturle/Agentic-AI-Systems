output "search_service_name" {
  description = "Search service name."
  value       = azurerm_search_service.knowledge.name
}

output "search_service_id" {
  description = "ARM resource ID of the search service."
  value       = azurerm_search_service.knowledge.id
}

output "index_name" {
  description = "Index name the retrieve tool queries. Published, not enforced — Terraform cannot create the index. Must match index-schema.json."
  value       = var.index_name
}

output "search_endpoint" {
  description = "Data-plane endpoint the retrieve tool queries. Injected into the tool as KNOWLEDGE_ENDPOINT."
  value       = "https://${azurerm_search_service.knowledge.name}.search.windows.net"
}

output "identity_principal_id" {
  description = "The service's own system-assigned identity, for granting it access to a customer-managed key or an identity-authenticated data source."
  value       = azurerm_search_service.knowledge.identity[0].principal_id
}

output "local_authentication_enabled" {
  description = <<-DESC
    Whether API keys are live on this service. Surfaced as an output so it can be asserted
    in review rather than assumed: with this true, every role assignment in this module is
    advisory, because an admin key bypasses all of them.
  DESC
  value       = azurerm_search_service.knowledge.local_authentication_enabled
}

output "private_endpoint_id" {
  description = "Private endpoint ID, or null when the service is reachable only over its public endpoint."
  value       = length(azurerm_private_endpoint.knowledge) > 0 ? azurerm_private_endpoint.knowledge[0].id : null
}
