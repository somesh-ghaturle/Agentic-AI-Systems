output "workflow_id" {
  description = "Full workflow resource ID."
  value       = google_workflows_workflow.orchestrator.id
}

output "workflow_name" {
  description = "Workflow name. Deterministic from name_prefix, which is why callers can compute it before this module runs and pass it to modules/observability without creating a cycle."
  value       = google_workflows_workflow.orchestrator.name
}

output "workflow_revision_id" {
  description = "Revision ID of the deployed definition. Changes on every source edit — useful for confirming that the workflow running is the one you just applied."
  value       = google_workflows_workflow.orchestrator.revision_id
}

output "deny_policy_id" {
  description = <<-EOT
    IAM Deny policy resource ID, or null when no write tools were supplied.

    Null here means lock 2 does not exist. That is correct only if the system genuinely has
    no write tools; otherwise the write boundary is resting on modules/tools alone.
  EOT
  value       = length(google_iam_deny_policy.write_boundary) > 0 ? google_iam_deny_policy.write_boundary[0].id : null
}

output "write_boundary_denied_services" {
  description = "Cloud Run services the orchestrator is explicitly denied invoke on. Surfaced so it can be asserted in review rather than assumed — this list should exactly equal the write tools."
  value       = var.write_tool_service_names
}
