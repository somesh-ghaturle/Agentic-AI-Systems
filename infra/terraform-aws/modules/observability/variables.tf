variable "name_prefix" {
  description = "Prefix for resource names, typically \"<project>-<env>\"."
  type        = string
}

variable "log_retention_days" {
  description = "Retention for the trace log group. Traces feed evaluation and incident investigation, so this is usually longer than ordinary application logs."
  type        = number
  default     = 90
}

variable "daily_cost_threshold_usd" {
  description = "Alarm when a day's summed request cost exceeds this. Null disables. Set it from observed spend plus headroom, not from a guess."
  type        = number
  default     = null
}

variable "schema_failure_threshold" {
  description = "Alarm when structured-output validation failures in five minutes exceed this. Null disables."
  type        = number
  default     = 5
}

variable "execution_failure_threshold" {
  description = "Alarm when orchestrator failures in five minutes exceed this."
  type        = number
  default     = 5
}

variable "state_machine_arn" {
  description = "Orchestrator state machine ARN, for execution-level alarms and for permitting the orchestrator to invoke the trace emitter."
  type        = string
  default     = null
}

variable "trace_emitter" {
  description = <<-EOT
    The function the orchestrator invokes to write its own trace records.

    Null omits it, which leaves the loop-bound and terminal-record filters watching a log
    group the state machine cannot write to. Those two alarms then sit permanently at
    zero, which reads as healthy. Supply it unless something else in your system already
    ships orchestrator-level traces to this group.

    Source: src/emit_trace.
  EOT

  type = object({
    handler         = string
    runtime         = string
    package_path    = string
    timeout_seconds = optional(number, 10)
    memory_mb       = optional(number, 256)
  })

  default = null
}

variable "alarm_topic_arns" {
  description = "SNS topics notified when an alarm fires."
  type        = list(string)
  default     = []
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
