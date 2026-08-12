variable "project_id" {
  description = "GCP project."
  type        = string
}

variable "name_prefix" {
  description = "Prefix for resource names, typically \"<project>-<env>\"."
  type        = string
}

variable "location" {
  description = "Region for the trace emitter function and its source bucket."
  type        = string
}

variable "trace_emitter" {
  description = <<-EOT
    The trace emitter function, or null to omit it.

    Omitting it is supported and is almost always a mistake. The orchestrator's own
    records — terminal outcome, loop bound, cost — reach the log-based metrics only
    through this function, so without it the loop-bound and spend alerts sit at zero
    forever, which is indistinguishable from a healthy system.
  EOT

  type = object({
    package_path          = string
    service_account_email = string
    member                = string
    orchestrator_member   = string
    runtime               = optional(string, "python312")
    entry_point           = optional(string, "handler")
  })

  default = null
}

variable "trace_writer_members" {
  description = "Principals granted roles/logging.logWriter, keyed by name. Must include every handler that emits traces — one missing and that handler's records never appear, while the handler itself reports success."
  type        = map(string)
  default     = {}
}

variable "alert_email_receivers" {
  description = "Email notification channels, keyed by name. Empty means the alert policies exist and notify nobody."
  type        = map(string)
  default     = {}
}

variable "schema_failure_threshold" {
  description = "Schema validation failures in a five-minute window before alerting. Not zero: an occasional failure is normal, a sustained rate is a broken prompt or a changed model."
  type        = number
  default     = 5
}

variable "abandoned_approval_threshold" {
  description = "Abandoned approvals in an hour before alerting on gate fatigue."
  type        = number
  default     = 2
}

variable "daily_cost_threshold_usd" {
  description = "Model spend over a day before alerting. In dev this is a runaway-loop detector, not a budget."
  type        = number
  default     = 25
}

variable "workflow_name" {
  description = "Orchestrator workflow name, for the execution-failure alert. Null omits that alert."
  type        = string
  default     = null
}

variable "workflow_failure_threshold" {
  description = "Failed workflow executions in a five-minute window before alerting."
  type        = number
  default     = 0
}

variable "archive_bucket_name" {
  description = "Bucket receiving archived traces. Null omits the sink. The sink's writer identity needs objectCreator on it — see the writer_identity output."
  type        = string
  default     = null
}

variable "ingress_settings" {
  description = "Cloud Run ingress for the trace emitter."
  type        = string
  default     = "ALLOW_ALL"
}

variable "labels" {
  description = "Labels applied to every resource in this module that supports them."
  type        = map(string)
  default     = {}
}
