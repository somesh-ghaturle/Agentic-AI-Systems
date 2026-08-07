output "trace_log_group_name" {
  description = <<-EOT
    Trace log group. The metric filters in this module expect JSON records with these
    fields — PRODUCTION-PRINCIPLES.md "Log full execution traces":

      correlation_id   tying every step of one request together
      event_type       "step_complete" | "request_complete" | "schema_validation_failed"
                       | "loop_bound_exceeded"
      step             step name or index
      model_version    without this, results are not reproducible
      prompt_version   same
      input_tokens     per call
      output_tokens    per call
      total_tokens     on the terminal record
      cost_usd         on the terminal record
      latency_ms       per step and end-to-end
      outcome          success | failure | abandoned | rejected | escalated

    Emitting these is application work. The filters match nothing without them.

    Handlers write here directly. The orchestrator cannot — a state machine logs to its
    own execution group — so its records come through the trace_emitter function in this
    module. Two of the four filters below depend entirely on it.
  EOT
  value       = aws_cloudwatch_log_group.traces.name
}

output "trace_log_group_arn" {
  description = "Trace log group ARN, for granting write access."
  value       = aws_cloudwatch_log_group.traces.arn
}

output "trace_emitter_arn" {
  description = "Trace emitter ARN. Pass to the orchestration module's tool_function_arns so the state machine may invoke it, and reference it from the terminal states of your definition."
  value       = try(aws_lambda_function.trace_emitter[0].arn, null)
}

output "trace_emitter_function_name" {
  description = "Trace emitter function name, for the state machine definition."
  value       = try(aws_lambda_function.trace_emitter[0].function_name, null)
}

output "metric_namespace" {
  description = "CloudWatch namespace holding cost, token, and failure metrics."
  value       = local.metric_namespace
}
