output "state_machine_arn" {
  description = "Orchestrator state machine ARN."
  value       = aws_sfn_state_machine.orchestrator.arn
}

output "role_arn" {
  description = "Orchestrator execution role ARN — grant this principal access to the knowledge collection and any other data plane."
  value       = aws_iam_role.orchestrator.arn
}

output "log_group_name" {
  description = "CloudWatch log group holding execution traces."
  value       = aws_cloudwatch_log_group.orchestrator.name
}
