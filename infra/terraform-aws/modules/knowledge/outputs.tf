output "collection_endpoint" {
  description = "Collection endpoint for the retrieval client."
  value       = aws_opensearchserverless_collection.knowledge.collection_endpoint
}

output "collection_arn" {
  description = "Collection ARN, for least-privilege IAM policies."
  value       = aws_opensearchserverless_collection.knowledge.arn
}

output "collection_id" {
  description = "Collection ID."
  value       = aws_opensearchserverless_collection.knowledge.id
}
