output "approvals_table" {
  description = "Fully qualified approvals table."
  value       = local.approvals_table
}

output "submit_procedure" {
  description = "Signature the orchestrator calls to propose a write."
  value       = local.procedures["submit"]
}

output "claim_procedure" {
  description = "Signature the executor calls to claim an approved proposal."
  value       = local.procedures["claim"]
}

output "approve_procedure" {
  description = "Signature a human approver calls. Granted to no machine role."
  value       = local.procedures["approve"]
}

output "stale_claim_seconds" {
  description = "The reclaim window, surfaced so handlers can align their own timeouts beneath it."
  value       = var.stale_claim_seconds
}
