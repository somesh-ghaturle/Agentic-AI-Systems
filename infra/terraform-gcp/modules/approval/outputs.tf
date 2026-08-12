output "validator_url" {
  description = "Validator function URL, for the orchestrator to call."
  value       = google_cloudfunctions2_function.validator.service_config[0].uri
}

output "executor_url" {
  description = "Executor function URL. Reached by an approver resolving an approval, and by nothing else."
  value       = google_cloudfunctions2_function.executor.service_config[0].uri
}

output "validator_function_name" {
  description = "Validator Cloud Run service name, for log filters and alert policies."
  value       = google_cloudfunctions2_function.validator.name
}

output "executor_function_name" {
  description = "Executor Cloud Run service name."
  value       = google_cloudfunctions2_function.executor.name
}

output "approvals_database_name" {
  description = "Firestore database holding approval records."
  value       = google_firestore_database.approvals.name
}

output "approval_topic_id" {
  description = "Pub/Sub topic carrying approval requests."
  value       = google_pubsub_topic.approval_requests.id
}

output "approval_topic_name" {
  description = "Short name of the approval topic."
  value       = google_pubsub_topic.approval_requests.name
}

output "function_names" {
  description = "Both approval function names keyed by role, for observability wiring."
  value = {
    "approval-validator" = google_cloudfunctions2_function.validator.name
    "approval-executor"  = google_cloudfunctions2_function.executor.name
  }
}
