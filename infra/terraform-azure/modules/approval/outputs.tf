output "executor_principal_id" {
  description = <<-DESC
    Object ID of the executor's managed identity.

    modules/tools consumes this to grant the invoke app role on write tools. It is the
    only value that opens that path, which is why it is a single scalar rather than a
    list — there is no shape here that admits a second principal by accident.
  DESC
  value       = var.executor_identity.principal_id
}

output "validator_url" {
  description = "Validator invocation URL. The orchestrator calls this before any human is asked."
  value       = "https://${azurerm_linux_function_app.approval["validator"].default_hostname}/api/validate"
}

output "executor_url" {
  description = "Executor invocation URL. Called by the approver's action, not by the orchestrator."
  value       = "https://${azurerm_linux_function_app.approval["executor"].default_hostname}/api/execute"
}

output "approval_topic_id" {
  description = "Service Bus topic carrying approval requests."
  value       = azurerm_servicebus_topic.approval.id
}

output "approval_topic_name" {
  description = "Topic name, for the validator's app settings."
  value       = azurerm_servicebus_topic.approval.name
}

output "cosmos_endpoint" {
  description = "Cosmos account endpoint for the approvals container."
  value       = azurerm_cosmosdb_account.approvals.endpoint
}

output "cosmos_account_id" {
  description = "Cosmos account resource ID, for diagnostic settings and private endpoints."
  value       = azurerm_cosmosdb_account.approvals.id
}

output "function_app_ids" {
  description = "Validator and executor function app IDs, for diagnostic settings."
  value       = { for k, app in azurerm_linux_function_app.approval : k => app.id }
}

output "function_app_names" {
  description = "Validator and executor function app names, for alarm scoping."
  value       = { for k, app in azurerm_linux_function_app.approval : k => app.name }
}
