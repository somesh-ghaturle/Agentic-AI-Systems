output "read_tool_urls" {
  description = "URLs of read tools, keyed by name — safe to hand the orchestrator."
  value       = { for k, v in google_cloudfunctions2_function.tool : k => v.service_config[0].uri if var.tools[k].access == "read" }
}

output "write_tool_urls" {
  description = "URLs of write tools, keyed by name — invoked only by the approval executor, never by the orchestrator. This output should have exactly one consumer; a second one appearing means something other than the executor intends to call a write tool."
  value       = { for k, v in google_cloudfunctions2_function.tool : k => v.service_config[0].uri if var.tools[k].access == "write" }
}

output "tool_urls_by_name" {
  description = "Every tool URL keyed by name."
  value       = { for k, v in google_cloudfunctions2_function.tool : k => v.service_config[0].uri }
}

output "write_tool_service_names" {
  description = <<-EOT
    Cloud Run service names backing the write tools.

    Consumed by modules/orchestration to build the IAM Deny policy — the second lock.
    A deny rule needs to name the resources it applies to, and the Cloud Run service name
    is what appears in `resource.name` at evaluation time.
  EOT
  value       = [for k, v in google_cloudfunctions2_function.tool : v.name if var.tools[k].access == "write"]
}

output "function_names" {
  description = "Every function name keyed by tool name, for log filters and alert policies."
  value       = { for k, v in google_cloudfunctions2_function.tool : k => v.name }
}

output "source_bucket_name" {
  description = "Bucket holding staged deployment packages."
  value       = google_storage_bucket.source.name
}
