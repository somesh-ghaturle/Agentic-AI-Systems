output "state_machine_arn" {
  description = "Step Functions ARN, or null while resources are disabled."
  value       = try(aws_sfn_state_machine.orchestrator[0].arn, null)
}
