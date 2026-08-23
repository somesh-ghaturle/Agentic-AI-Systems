variable "project" {
  description = "Project name. Combined with the environment to prefix every resource."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9-]{1,13}$", var.project))
    error_message = "project must be lowercase alphanumeric/hyphens and at most 13 chars, so \"<project>-staging-knowledge\" stays within the 32-char OpenSearch collection name limit. This is three characters tighter than prod allows, because \"staging\" is three characters longer than \"prod\" — a project name that fits prod may not fit here."
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
# Network — required, because the knowledge collection is never public in staging
#
# Same requirement as prod, and the reason staging exists. These being wrong is a failure
# that cannot surface in dev, where the collection is public.
# ---------------------------------------------------------------------------

variable "vpc_id" {
  description = "VPC hosting the knowledge collection endpoint."
  type        = string
}

variable "subnet_ids" {
  description = "Subnets for the collection endpoint. Use private subnets — the same ones prod will use, or the rehearsal proves nothing about prod's routing."
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

variable "trace_emitter" {
  description = "The function the orchestrator invokes to write its own trace records. Source: src/emit_trace."

  type = object({
    handler         = string
    runtime         = string
    package_path    = string
    timeout_seconds = optional(number, 10)
    memory_mb       = optional(number, 256)
  })

  # Required, as in prod. Without it the loop-bound and cost alarms sit permanently at zero
  # and report nothing — and an alarm that silently cannot fire is precisely the defect a
  # staging environment is supposed to catch before prod inherits it.
  nullable = false
}

# ---------------------------------------------------------------------------
# Retention
#
# Dev-scale, not prod-scale. Retention buys the ability to investigate something later,
# and nothing in staging is investigated later — the next release replaces it.
# ---------------------------------------------------------------------------

variable "log_retention_days" {
  description = "Retention for orchestrator, tool, and trace logs."
  type        = number
  default     = 30
}

variable "approval_log_retention_days" {
  description = "Retention for approval-gate logs. Longer than ordinary logs, as in prod, but months rather than years — these reconstruct a failed rehearsal, not an audit."
  type        = number
  default     = 90
}

variable "archive_expiration_days" {
  description = "Days before archived traces are deleted. Unlike prod this has a finite default and null is rejected: an environment that is rebuilt regularly must not accumulate an archive nothing expires."
  type        = number
  default     = 90

  # nullable = false rather than a null check in the condition below: prod accepts null and
  # means "retain indefinitely", so null is the value most likely to be copied across from
  # prod's tfvars, and it should be refused by the type system rather than by a rule that
  # has to evaluate `null > 0`.
  nullable = false

  validation {
    condition     = var.archive_expiration_days > 0
    error_message = "staging must expire its trace archive. Null retains indefinitely, which is a prod decision made from a records policy — staging has no such policy and no reader for old traces."
  }
}

# Deliberately absent: archive_object_lock_days.
#
# Prod exposes Object Lock as a variable. Staging does not, and the omission is the point.
# Lock mode must be chosen before the bucket exists and COMPLIANCE retention cannot be
# shortened by anyone afterwards, including the root account. Exposing it here would let a
# single tfvars line permanently strand the bucket of the one environment whose value
# depends on being destroyable. modules/archive receives a hard-coded null in main.tf.

# ---------------------------------------------------------------------------
# Security and alarms
# ---------------------------------------------------------------------------

variable "create_guardrail" {
  description = "Create a Bedrock guardrail. Only applicable when the model layer runs on Bedrock. Reversible, so it belongs on whatever prod will run — turn it on here first."
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
  description = "Alarm when a day's summed request cost exceeds this. Lower than prod on purpose: staging load is a rehearsal, so an unexpected day's spend here is a runaway loop rather than growth."
  type        = number
  default     = 50
}

variable "alarm_topic_arns" {
  description = "SNS topics notified when an alarm fires. Required here as in prod — routing alarms is itself a thing worth rehearsing, and it cannot be rehearsed if the list is empty."
  type        = list(string)

  validation {
    condition     = length(var.alarm_topic_arns) > 0
    error_message = "At least one alarm topic is required. Whether an alarm reaches a human is part of what staging verifies; an empty list here means prod's alarm routing gets its first test in prod."
  }
}
