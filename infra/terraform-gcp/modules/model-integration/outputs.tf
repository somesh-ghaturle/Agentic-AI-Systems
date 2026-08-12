output "model_id" {
  description = "Model identifier for handler configuration."
  value       = var.model_id
}

output "vertex_location" {
  description = "Region handlers should target for Vertex AI calls."
  value       = var.location
}

output "vertex_endpoint" {
  description = "Regional Vertex AI endpoint host."
  value       = "${var.location}-aiplatform.googleapis.com"
}
