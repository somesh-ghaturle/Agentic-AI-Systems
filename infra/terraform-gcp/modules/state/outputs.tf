output "database_name" {
  description = "Firestore database name, as handlers reference it."
  value       = google_firestore_database.state.name
}

output "database_id" {
  description = "Full Firestore database resource ID."
  value       = google_firestore_database.state.id
}

output "executions_collection" {
  description = "Collection holding execution records."
  value       = var.executions_collection
}
