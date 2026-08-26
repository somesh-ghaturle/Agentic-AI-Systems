output "database_name" {
  description = "Database holding the stack."
  value       = module.state.database_name
}

output "warehouse_name" {
  description = "Warehouse every handler runs on."
  value       = module.state.warehouse_name
}

output "write_tool_signatures" {
  description = "Write tools. Callable by the executor role and nothing else."
  value       = module.tools.write_tool_signatures
}

output "approvals_table" {
  description = "The approval record — concurrency control and audit trail."
  value       = module.approval.approvals_table
}

output "search_service_name" {
  description = "Cortex Search service backing retrieval."
  value       = module.knowledge.search_service_name
}

output "traces_table" {
  description = "Structured agent traces."
  value       = module.observability.traces_table
}

output "service_user_names" {
  description = "Service users, all federated. None carries a credential."
  value       = module.identity.service_user_names
}
