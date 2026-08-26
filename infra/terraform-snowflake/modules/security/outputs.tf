output "tool_owner_role" {
  description = "Role owning write procedures and holding the underlying table privileges. Granted to no user."
  value       = snowflake_account_role.tool_owner.name
}

output "orchestrator_role" {
  description = "The agent loop's role. Read tools only."
  value       = snowflake_account_role.orchestrator.name
}

output "validator_role" {
  description = "Role that writes approval records."
  value       = snowflake_account_role.validator.name
}

output "executor_role" {
  description = "The only role holding USAGE on write procedures."
  value       = snowflake_account_role.executor.name
}

output "auditor_role" {
  description = "Read-only role over the AUDIT schema."
  value       = snowflake_account_role.auditor.name
}

output "network_policy_name" {
  description = "Network policy to attach to the service users, or null when no allow-list was supplied."
  value       = one(snowflake_network_policy.main[*].name)
}

output "email_masking_policy" {
  description = "Fully qualified email masking policy, or null when masking is disabled."
  value       = var.create_masking_policies ? "${var.database_name}.${var.audit_schema}.${snowflake_masking_policy.email[0].name}" : null
}

output "task_owner_role" {
  description = "Role owning the approval sweeper task. Inherits the executor role; granted to no user."
  value       = snowflake_account_role.task_owner.name
}
