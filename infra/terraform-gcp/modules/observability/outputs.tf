output "trace_log_name" {
  description = "Shared trace log name. Every handler writes structured entries here; nothing else is visible to the metrics."
  value       = local.trace_log_name
}

output "trace_log_filter" {
  description = "The logName filter every metric in this module uses. Useful for reproducing an alert's query by hand."
  value       = local.trace_filter
}

output "trace_emitter_url" {
  description = "Trace emitter URL for the orchestrator to call, or null when the emitter is omitted."
  value       = var.trace_emitter == null ? null : google_cloudfunctions2_function.trace_emitter[0].service_config[0].uri
}

output "trace_emitter_function_name" {
  description = "Trace emitter Cloud Run service name, or null when omitted."
  value       = var.trace_emitter == null ? null : google_cloudfunctions2_function.trace_emitter[0].name
}

output "sink_writer_identity" {
  description = <<-EOT
    Service account the log sink writes as, or null when no archive bucket was supplied.

    This principal needs objectCreator on the archive bucket. Until it has that, the sink
    exists, reports no error, and delivers nothing — pass this into the archive module's
    writer_members.
  EOT
  value       = var.archive_bucket_name == null ? null : google_logging_project_sink.archive[0].writer_identity
}

output "metric_names" {
  description = "Log-based metric names, for reproducing an alert query or checking one is receiving data."
  value = {
    schema_validation_failed = google_logging_metric.schema_validation_failed.name
    loop_bound_exceeded      = google_logging_metric.loop_bound_exceeded.name
    approval_abandoned       = google_logging_metric.approval_abandoned.name
    cost_usd                 = google_logging_metric.cost_usd.name
  }
}
