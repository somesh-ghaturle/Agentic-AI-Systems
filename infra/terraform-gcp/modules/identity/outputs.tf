output "identities" {
  description = "Every workload service account keyed by account ID. Consumers take `email` for IAM bindings and `name` for impersonation grants."
  value       = google_service_account.workload
}

output "emails" {
  description = "Service account emails keyed by account ID — the form IAM members take."
  value       = { for k, v in google_service_account.workload : k => v.email }
}

output "members" {
  description = "Service account principals already in `serviceAccount:<email>` form, ready to drop into an IAM binding."
  value       = { for k, v in google_service_account.workload : k => "serviceAccount:${v.email}" }
}
