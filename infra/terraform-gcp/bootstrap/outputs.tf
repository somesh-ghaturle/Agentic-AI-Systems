output "state_bucket" {
  description = "Bucket name for the `bucket` argument of each environment's backend block."
  value       = google_storage_bucket.state.name
}

output "backend_block" {
  description = "The backend block to paste into an environment root, with `<env>` replaced."
  value       = <<-EOT
    backend "gcs" {
      bucket = "${google_storage_bucket.state.name}"
      prefix = "agentic/<env>"
    }
  EOT
}
