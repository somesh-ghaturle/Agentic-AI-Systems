output "tool_uri" {
  description = "Internal GCP function URI."
  value       = try(google_cloudfunctions2_function.tool[0].service_config[0].uri, null)
}
