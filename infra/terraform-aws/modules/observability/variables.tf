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
  description = "Orchestrator state machine ARN, for execution-level alarms."
  type        = string
  default     = null
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
