output "state_machine_arn" {
  description = "Orchestrator state machine ARN."
  value       = module.orchestration.state_machine_arn
}

output "execution_state_table" {
  description = "Execution state table name."
  value       = module.state.table_name
}

output "trace_archive_bucket" {
  description = "Trace archive bucket."
  value       = module.archive.bucket_id
}

output "knowledge_endpoint" {
  description = "Knowledge collection endpoint for the retrieval client."
  value       = module.knowledge.collection_endpoint
}

output "trace_log_group" {
  description = "Trace log group. See modules/observability/outputs.tf for the field schema the metric filters expect."
  value       = module.observability.trace_log_group_name
}

output "approvals_table" {
  description = "Approval audit table — proposal, validation, approver, outcome."
  value       = module.approval.approvals_table_name
}

output "kms_key_arn" {
  description = "Customer-managed key protecting data at rest."
  value       = module.security.kms_key_arn
}

# The read/write split, surfaced so it can be asserted in review rather than assumed.
# Anything in write_tools must be unreachable by the orchestrator.
output "read_tools" {
  description = "Tools the orchestrator may invoke directly."
  value       = module.tools.read_tool_arns
}

output "write_tools" {
  description = "Tools only the approval executor may invoke. The orchestrator cannot reach these."
  value       = module.tools.write_tool_arns
}
