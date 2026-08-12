output "workflow_name" {
  description = "Orchestrator workflow. Start an execution with `gcloud workflows run`."
  value       = module.orchestration.workflow_name
}

output "execution_state_database" {
  description = "Firestore database holding one document per execution."
  value       = module.state.database_name
}

output "trace_archive_bucket" {
  description = "Trace archive bucket."
  value       = module.archive.bucket_name
}

output "trace_archive_locked" {
  description = "Whether the archive's retention policy is locked. False here, which is correct for dev and wrong for an audit trail — prod locks it."
  value       = module.archive.retention_locked
}

output "knowledge_index_endpoint" {
  description = "Vector Search index endpoint the retrieve handler queries."
  value       = module.knowledge.index_endpoint_id
}

output "trace_log_name" {
  description = "Shared trace log. Handlers that write anywhere else are invisible to every alert — see modules/observability/outputs.tf for the field schema the metrics expect."
  value       = module.observability.trace_log_name
}

output "approvals_database" {
  description = "Firestore database holding the record of who authorized what."
  value       = module.approval.approvals_database_name
}

output "kms_key_id" {
  description = "Customer-managed key protecting data at rest."
  value       = module.security.kms_key_id
}

# ---------------------------------------------------------------------------
# The write boundary, surfaced so it can be asserted in review rather than assumed.
#
# Nothing in `read_tools` should mutate state, and nothing in `write_tools` should be
# reachable by the orchestrator. The third output is the second lock: it should list
# exactly the same services as the second.
# ---------------------------------------------------------------------------

output "read_tools" {
  description = "Tools the orchestrator may invoke directly."
  value       = module.tools.read_tool_urls
}

output "write_tools" {
  description = "Tools only the approval executor may invoke. The orchestrator holds no run.invoker on these and is separately denied it."
  value       = module.tools.write_tool_urls
}

output "write_boundary_denied_services" {
  description = "Services the IAM Deny policy names. Should equal the keys of write_tools; a shorter list means part of the write path rests on lock 1 alone."
  value       = module.orchestration.write_boundary_denied_services
}

output "service_accounts" {
  description = "Every workload identity, keyed by account ID. One per workload — a shared identity would make every data-plane grant a grant to everything."
  value       = module.identity.emails
}
