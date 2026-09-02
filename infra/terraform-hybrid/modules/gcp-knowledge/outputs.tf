output "index_id" {
  description = "Vertex AI index ID, or null while resources are disabled."
  value       = try(google_vertex_ai_index.knowledge[0].id, null)
}
