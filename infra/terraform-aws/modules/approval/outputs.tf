output "executor_arn" {
  description = "Approval executor ARN. Pass to the tools module as approval_executor_arn — it is the only principal permitted to invoke write tools."
  value       = aws_lambda_function.executor.arn
}

output "validator_arn" {
  description = "Approval validator ARN, invoked by the orchestrator to validate a proposed write."
  value       = aws_lambda_function.validator.arn
}

output "approval_topic_arn" {
  description = "SNS topic carrying approval requests to human reviewers."
  value       = aws_sns_topic.approval_requests.arn
}

output "approvals_table_name" {
  description = "Approval audit table — proposal, validation result, approver, outcome."
  value       = aws_dynamodb_table.approvals.name
}

output "approvals_table_arn" {
  description = "Approval audit table ARN."
  value       = aws_dynamodb_table.approvals.arn
}
