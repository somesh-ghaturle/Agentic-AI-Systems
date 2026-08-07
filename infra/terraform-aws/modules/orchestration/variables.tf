variable "name_prefix" {
  description = "Prefix for resource names, typically \"<project>-<env>\"."
  type        = string
}

variable "definition" {
  description = <<-EOT
    Amazon States Language definition, as JSON.

    The flow is the application, so this module does not own it. What the definition must
    provide, per BUILDING-BLOCKS.md §4 "Non-negotiables":

      - A bounded loop: a step counter checked against a maximum, plus TimeoutSeconds on
        the state machine. An unbounded agent loop is a billing incident.
      - Retry and Catch on every task state, with the failure path chosen deliberately.
      - A correlation ID threaded through every state.
      - waitForTaskToken on any state fronting a high-impact write.

    See HOW-TO-DEPLOY.md for a worked definition showing all four.
  EOT
  type        = string
}

variable "state_machine_type" {
  description = "STANDARD gives full execution history and supports waitForTaskToken (required for approval gates). EXPRESS is cheaper and faster but caps at five minutes and keeps no history — unsuitable for a workflow with a human in it."
  type        = string
  default     = "STANDARD"

  validation {
    condition     = contains(["STANDARD", "EXPRESS"], var.state_machine_type)
    error_message = "state_machine_type must be STANDARD or EXPRESS."
  }
}

variable "log_execution_data" {
  description = "Include state input/output in logs. Invaluable for debugging and a PII exposure if payloads are not masked upstream — see the privacy note in HOW-TO-DEPLOY.md."
  type        = bool
  default     = false
}

variable "log_retention_days" {
  description = "CloudWatch retention for orchestrator logs."
  type        = number
  default     = 90
}

variable "tool_function_arns" {
  description = "Lambda ARNs the orchestrator may invoke. Scoped deliberately — no blanket lambda:InvokeFunction."
  type        = list(string)
  default     = []
}

variable "state_table_arn" {
  description = "Execution state table ARN, from the state module."
  type        = string
  default     = null
}

variable "archive_bucket_arn" {
  description = "Trace archive bucket ARN, from the archive module. Granted PutObject only — never delete."
  type        = string
  default     = null
}

variable "approval_topic_arn" {
  description = "SNS topic ARN, from the approval module."
  type        = string
  default     = null
}

variable "kms_key_arn" {
  description = "Customer-managed KMS key ARN for log encryption."
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags applied to every resource in this module."
  type        = map(string)
  default     = {}
}
