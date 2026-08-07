variable "project" {
  description = "Project name. Combined with the environment to prefix every resource."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9-]{1,16}$", var.project))
    error_message = "project must be lowercase alphanumeric/hyphens and at most 16 chars, so \"<project>-prod-knowledge\" stays within the 32-char OpenSearch collection name limit."
  }
}

variable "region" {
  description = "AWS region."
  type        = string
  default     = "us-east-1"
}

variable "data_classification" {
  description = "Data classification for this deployment, surfaced as a tag. In a governed environment this drives which controls apply — see ENTERPRISE-ADAPTATION.md."
  type        = string
  default     = "internal"
}

# ---------------------------------------------------------------------------
# Network — required, because the knowledge collection is never public in prod
# ---------------------------------------------------------------------------

variable "vpc_id" {
  description = "VPC hosting the knowledge collection endpoint."
  type        = string
}

variable "subnet_ids" {
  description = "Subnets for the collection endpoint. Use private subnets."
  type        = list(string)

  validation {
    condition     = length(var.subnet_ids) > 0
    error_message = "At least one subnet is required."
  }
}

variable "security_group_ids" {
  description = "Security groups for the collection endpoint."
  type        = list(string)
  default     = []
}

# ---------------------------------------------------------------------------
# Tools and approval gate
# ---------------------------------------------------------------------------

variable "tools" {
  description = "Tool definitions. See modules/tools/variables.tf. Classify `access` by what the handler does, not by its name."

  type = map(object({
    access               = string
    handler              = string
    runtime              = string
    package_path         = string
    timeout_seconds      = number
    memory_mb            = optional(number, 512)
    reserved_concurrency = optional(number, -1)
    environment          = optional(map(string), {})
    policy_json          = optional(string)
  }))

  default = {}
}

variable "approval_validator" {
  description = "Validator function — deterministic ownership, permission, and limit checks."

  type = object({
    handler         = string
    runtime         = string
    package_path    = string
    timeout_seconds = number
    memory_mb       = optional(number, 512)
    environment     = optional(map(string), {})
  })
}

variable "approval_executor" {
  description = "Executor function — the only principal permitted to invoke write tools."

  type = object({
    handler              = string
    runtime              = string
    package_path         = string
    timeout_seconds      = number
    memory_mb            = optional(number, 512)
    reserved_concurrency = optional(number, 10)
    environment          = optional(map(string), {})
  })
}

# ---------------------------------------------------------------------------
# Retention
# ---------------------------------------------------------------------------

variable "log_retention_days" {
  description = "Retention for orchestrator, tool, and trace logs."
  type        = number
  default     = 365
}

variable "approval_log_retention_days" {
  description = "Retention for approval-gate logs. Longer than ordinary logs — these are audit evidence."
  type        = number
  default     = 2555 # 7 years
}

variable "archive_expiration_days" {
  description = "Days before archived traces are deleted. Null retains indefinitely. Comes from your records policy, not from a default."
  type        = number
  default     = null
}

variable "archive_object_lock_days" {
  description = <<-EOT
    Enables S3 Object Lock in COMPLIANCE mode for this many days. Null disables.

    Set only in an audit context, and understand both consequences first: it must be
    decided before the bucket is created, and once set, nobody — including the root
    account — can shorten or override the retention window.
  EOT
  type        = number
  default     = null
}

# ---------------------------------------------------------------------------
# Security and alarms
# ---------------------------------------------------------------------------

variable "create_guardrail" {
  description = "Create a Bedrock guardrail. Only applicable when the model layer runs on Bedrock."
  type        = bool
  default     = false
}

variable "pii_entities" {
  description = "PII entities to mask at the model boundary. A backstop for what upstream masking missed — not a replacement for masking before data leaves your boundary."
  type = list(object({
    type   = string
    action = string
  }))
  default = []
}

variable "daily_cost_threshold_usd" {
  description = "Alarm when a day's summed request cost exceeds this. Set from observed spend plus headroom."
  type        = number
  default     = null
}

variable "alarm_topic_arns" {
  description = "SNS topics notified when an alarm fires. Leaving this empty in prod means nobody hears an alarm."
  type        = list(string)

  validation {
    condition     = length(var.alarm_topic_arns) > 0
    error_message = "At least one alarm topic is required in prod. An alarm nobody receives is not monitoring."
  }
}
