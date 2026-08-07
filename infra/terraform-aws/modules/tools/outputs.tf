output "read_tool_arns" {
  description = "ARNs of read tools — safe to grant the orchestrator directly."
  value       = [for k, v in aws_lambda_function.tool : v.arn if var.tools[k].access == "read"]
}

output "write_tool_arns" {
  description = "ARNs of write tools — invoked only by the approval executor, never by the orchestrator."
  value       = [for k, v in aws_lambda_function.tool : v.arn if var.tools[k].access == "write"]
}

output "tool_arns_by_name" {
  description = "Every tool ARN keyed by name."
  value       = { for k, v in aws_lambda_function.tool : k => v.arn }
}

output "tool_role_arns_by_name" {
  description = "Every tool role ARN keyed by name, for granting data-plane access."
  value       = { for k, v in aws_iam_role.tool : k => v.arn }
}
