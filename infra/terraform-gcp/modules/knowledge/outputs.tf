output "index_id" {
  description = "Vector Search index resource ID."
  value       = google_vertex_ai_index.corpus.id
}

output "index_endpoint_id" {
  description = "Index endpoint resource ID. Handlers need this plus the deployed index ID to issue a query."
  value       = google_vertex_ai_index_endpoint.corpus.id
}

output "deployed_index_id" {
  description = "Deployed index ID, as the query API expects it."
  value       = google_vertex_ai_index_endpoint_deployed_index.corpus.deployed_index_id
}

output "public_endpoint_domain" {
  description = "Public serving domain for the endpoint. Empty until the first index finishes deploying."
  value       = google_vertex_ai_index_endpoint.corpus.public_endpoint_domain_name
}

output "corpus_bucket_name" {
  description = "Bucket holding the embedding files."
  value       = google_storage_bucket.corpus.name
}
