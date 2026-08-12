# The trace schema
#
# Terraform creates the destination, the routing, and the alerts. It cannot make handlers
# emit the fields those alerts read. Every query in this module parses each log line as
# JSON and filters on `event_type`, so a handler that prints unstructured text is
# invisible to all of them.
#
# Fields the alert queries depend on:
#
#   event_type    string   one of: request_complete, schema_validation_failed,
#                          loop_bound_exceeded, approval_abandoned
#   cost_usd      number   TERMINAL record only — per-step emission multiply-counts spend
#   total_tokens  number   terminal record only, same reason
#
# Fields the queries do not read but every trace should carry, because they are what make
# an incident reconstructable and cannot be added retroactively:
#
#   correlation_id, step, model_version, prompt_version, latency_ms, outcome

output "log_analytics_workspace_id" {
  description = "Workspace ID. Diagnostic settings and alert scopes point at this."
  value       = azurerm_log_analytics_workspace.law.id
}

output "log_analytics_workspace_name" {
  description = "Workspace name, for querying from the CLI or portal."
  value       = azurerm_log_analytics_workspace.law.name
}

output "action_group_id" {
  description = "Action group every alert in this module notifies."
  value       = azurerm_monitor_action_group.alerts.id
}

output "trace_emitter_url" {
  description = <<-DESC
    Endpoint the orchestrator calls to write its own trace records. Null when no trace
    emitter is configured — the workflow should treat that as a hard configuration error
    rather than skipping the call, since the alternative is a run nobody can audit.
  DESC
  value       = try("https://${azurerm_linux_function_app.trace_emitter[0].default_hostname}/api/trace", null)
}

output "trace_emitter_audience" {
  description = "Audience the orchestrator requests a token for when calling the trace emitter."
  value       = try("api://${var.name_prefix}-trace-emitter", null)
}
