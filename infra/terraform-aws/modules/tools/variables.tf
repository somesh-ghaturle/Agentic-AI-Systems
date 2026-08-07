variable "name_prefix" {
  description = "Prefix for resource names, typically \"<project>-<env>\"."
  type        = string
}

variable "tools" {
  description = <<-EOT
    Tool definitions, keyed by tool name.

    The `access` field is the load-bearing one. It decides who may invoke the function:

      read  → the orchestrator invokes directly
      write → ONLY the approval gate may invoke; the orchestrator can propose but not execute

    Classify honestly. A tool marked read that mutates state defeats the split entirely,
    and nothing in Terraform can detect that — it is a property of your handler code.

    Note that `timeout_seconds` and `reserved_concurrency` have no defaults by design.
    BUILDING-BLOCKS.md requires a timeout on every tool, so the module makes you state one.
  EOT

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

  validation {
    condition     = alltrue([for k, v in var.tools : contains(["read", "write"], v.access)])
    error_message = "Each tool's access must be \"read\" or \"write\"."
  }

  validation {
    condition     = alltrue([for k, v in var.tools : v.timeout_seconds > 0 && v.timeout_seconds <= 900])
    error_message = "Each tool needs a timeout between 1 and 900 seconds. Every external call gets one, no exceptions."
  }
}

variable "orchestrator_state_machine_arn" {
  description = "State machine ARN permitted to invoke read tools."
  type        = string
  default     = null
}

variable "approval_executor_arn" {
  description = "Approval executor Lambda ARN — the only principal permitted to invoke write tools. Required if any tool has access = \"write\"."
  type        = string
  default     = null
}

variable "common_environment" {
  description = "Environment variables merged into every tool. For values every handler needs — the trace log group, shared endpoints — rather than per-tool configuration."
  type        = map(string)
  default     = {}
}

variable "trace_log_group_name" {
  description = "Shared trace log group. Injected as TRACE_LOG_GROUP. Handlers that write traces to their own /aws/lambda group are invisible to every metric filter in the observability module."
  type        = string
  default     = null
}

variable "trace_log_group_arn" {
  description = "Shared trace log group ARN. Grants each tool role permission to write traces to it."
  type        = string
  default     = null
}

variable "log_retention_days" {
  description = "CloudWatch retention for tool logs."
  type        = number
  default     = 90
}

variable "kms_key_arn" {
  description = "Customer-managed KMS key ARN for environment variables and logs."
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags applied to every resource in this module."
  type        = map(string)
  default     = {}
}
