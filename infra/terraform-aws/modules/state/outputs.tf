output "table_name" {
  description = "Execution state table name, for the orchestrator's environment."
  value       = aws_dynamodb_table.execution_state.name
}

output "table_arn" {
  description = "Execution state table ARN, for least-privilege IAM policies."
  value       = aws_dynamodb_table.execution_state.arn
}
