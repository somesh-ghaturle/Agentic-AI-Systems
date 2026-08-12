output "bucket_name" {
  description = "Archive bucket name."
  value       = google_storage_bucket.archive.name
}

output "bucket_url" {
  description = "gs:// URL of the archive bucket."
  value       = google_storage_bucket.archive.url
}

output "retention_locked" {
  description = "Whether the retention policy is locked. False here means trace history is deletable, which is the correct answer for dev and the wrong one for an audit trail."
  value       = var.retention_days != null && var.lock_retention_policy
}
