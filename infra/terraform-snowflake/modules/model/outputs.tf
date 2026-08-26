output "complete_procedure" {
  description = "The guarded model entry point. The only one the orchestrator holds."
  value       = local.complete_signature
}

output "model_name" {
  description = "Cortex model backing the guarded entry point."
  value       = var.model_name
}
