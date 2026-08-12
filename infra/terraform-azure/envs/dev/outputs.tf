output "resource_group_name" {
  description = "Resource group holding the environment."
  value       = module.networking.resource_group_name
}

output "log_analytics_workspace_id" {
  description = "Workspace diagnostic settings should point at."
  value       = module.observability.log_analytics_workspace_id
}

output "action_group_id" {
  description = "Action group every alert notifies. Kept parallel with prod; envs/tenant should point at prod's, not this one."
  value       = module.observability.action_group_id
}

output "key_vault_uri" {
  description = "Vault URI. Workloads build Key Vault references from this."
  value       = module.security.keyvault_uri
}

output "read_tool_urls" {
  description = "Read tool endpoints — what the orchestrator calls."
  value       = module.tools.read_tool_urls
}

output "validator_url" {
  description = "Validator endpoint. The orchestrator calls this before any human is asked."
  value       = module.approval.validator_url
}

output "executor_url" {
  description = "Executor endpoint. Called by the approver's action, not by the orchestrator."
  value       = module.approval.executor_url
}

output "cosmos_endpoint" {
  description = "Cosmos account holding the approval records."
  value       = module.approval.cosmos_endpoint
}

output "orchestrator_workflow_name" {
  description = "Logic App the orchestrator runs as."
  value       = module.orchestration.logic_app_workflow_name
}

# Deliberately not output: write_tool_urls. The executor receives them through its app
# settings, and nothing else has a reason to know them. Publishing them here would put
# them in state output, in CI logs, and in front of anyone running `terraform output`.
