output "kms_key_arn" {
  description = "Customer-managed key ARN. Pass to every module that stores data at rest."
  value       = aws_kms_key.main.arn
}

output "kms_key_id" {
  description = "Customer-managed key ID."
  value       = aws_kms_key.main.key_id
}

output "guardrail_id" {
  description = "Bedrock guardrail ID, or null when create_guardrail is false."
  value       = var.create_guardrail ? aws_bedrock_guardrail.main[0].guardrail_id : null
}

output "guardrail_version" {
  description = "Pinned guardrail version. Reference this rather than DRAFT so a guardrail edit does not change production behavior until deployed deliberately."
  value       = var.create_guardrail ? aws_bedrock_guardrail_version.main[0].version : null
}
