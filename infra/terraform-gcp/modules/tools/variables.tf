variable "project_id" {
  description = "GCP project."
  type        = string
}

variable "name_prefix" {
  description = "Prefix for resource names, typically \"<project>-<env>\". The source bucket name derives from this and must be globally unique."
  type        = string
}

variable "location" {
  description = "Region for the functions and the source bucket."
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

    Note that `timeout_seconds` and `max_instances` have no defaults by design.
    BUILDING-BLOCKS.md requires a timeout on every tool, so the module makes you state one.
  EOT

  type = map(object({
    access          = string
    entry_point     = string
    runtime         = string
    package_path    = string
    timeout_seconds = number
    max_instances   = number
    memory_mb       = optional(number, 512)
    min_instances   = optional(number, 0)
    environment     = optional(map(string), {})
  }))

  default = {}

  validation {
    condition     = alltrue([for k, v in var.tools : contains(["read", "write"], v.access)])
    error_message = "Each tool's access must be \"read\" or \"write\"."
  }

  validation {
    condition     = alltrue([for k, v in var.tools : v.timeout_seconds > 0 && v.timeout_seconds <= 3600])
    error_message = "Each tool needs a timeout between 1 and 3600 seconds. Every external call gets one, no exceptions."
  }

  validation {
    condition     = alltrue([for k, v in var.tools : v.max_instances > 0])
    error_message = "Each tool needs a positive max_instances. An unbounded retry storm against a write path is how a confused agent becomes an incident."
  }
}

variable "tool_service_account_emails" {
  description = "Per-tool runtime service account emails, keyed by the same tool names as `tools`. One identity per tool: a shared identity makes every data-plane grant a grant to every tool."
  type        = map(string)

  validation {
    condition     = alltrue([for k, v in var.tool_service_account_emails : can(regex("@", v))])
    error_message = "Each value must be a service account email, not a member string. Pass `emails`, not `members`, from modules/identity."
  }
}

variable "orchestrator_member" {
  description = "Member string (`serviceAccount:...`) granted run.invoker on read tools. Never granted on write tools."
  type        = string
  default     = null
}

variable "approval_executor_member" {
  description = "Member string granted run.invoker on write tools — the only principal permitted to. Required if any tool has access = \"write\"."
  type        = string
  default     = null
}

variable "common_environment" {
  description = "Environment variables merged into every tool. For values every handler needs — the trace log name, shared endpoints — rather than per-tool configuration."
  type        = map(string)
  default     = {}
}

variable "trace_log_name" {
  description = "Shared trace log name. Injected as TRACE_LOG_NAME. Handlers that write traces to their own default log are invisible to every log-based metric in the observability module."
  type        = string
  default     = null
}

variable "ingress_settings" {
  description = "Cloud Run ingress. ALLOW_ALL means the URL resolves; IAM still decides who gets past it. ALLOW_INTERNAL_ONLY breaks invocation from Workflows without a VPC connector."
  type        = string
  default     = "ALLOW_ALL"

  validation {
    condition     = contains(["ALLOW_ALL", "ALLOW_INTERNAL_ONLY", "ALLOW_INTERNAL_AND_GCLB"], var.ingress_settings)
    error_message = "ingress_settings must be ALLOW_ALL, ALLOW_INTERNAL_ONLY, or ALLOW_INTERNAL_AND_GCLB."
  }
}

variable "kms_key_id" {
  description = "Customer-managed key for the source bucket."
  type        = string
  default     = null
}

variable "labels" {
  description = "Labels applied to every resource in this module that supports them."
  type        = map(string)
  default     = {}
}
