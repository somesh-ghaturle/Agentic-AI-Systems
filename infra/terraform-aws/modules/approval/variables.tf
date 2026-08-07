variable "name_prefix" {
  description = "Prefix for resource names, typically \"<project>-<env>\"."
  type        = string
}

variable "validator" {
  description = <<-EOT
    The validator function: deterministic checks that run before any human sees a proposal.

    What belongs in this handler, per BUILDING-BLOCKS.md §6:
      - Ownership: does the requesting user own the resource being acted on?
      - Permissions: is this actor allowed to take this action at all?
      - Limits: is the amount, count, or scope within policy?

    All of it in code, every time. The prompt is a hint; the code is the control.
  EOT

  type = object({
    handler         = string
    runtime         = string
    package_path    = string
    timeout_seconds = number
    memory_mb       = optional(number, 512)
    environment     = optional(map(string), {})
  })
}

variable "executor" {
  description = <<-EOT
    The executor function: invokes the approved write after verifying the task token.

    This is the only principal in the system permitted to call write tools. Its handler
    should verify the approval record, execute exactly the approved action with an
    idempotency key, record the outcome, and resolve the task token.
  EOT

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

variable "write_tool_arns" {
  description = "Write tool ARNs the executor may invoke. Enumerated deliberately — this list defines what a human approval can authorize."
  type        = list(string)
  default     = []
}

variable "orchestrator_state_machine_arn" {
  description = "State machine ARN whose task tokens this gate resolves."
  type        = string
  default     = null
}

variable "trace_log_group_name" {
  description = "Shared trace log group. Injected as TRACE_LOG_GROUP so approval events land where the metric filters can see them."
  type        = string
  default     = null
}

variable "trace_log_group_arn" {
  description = "Shared trace log group ARN. Grants the validator and executor roles permission to write traces."
  type        = string
  default     = null
}

variable "log_retention_days" {
  description = "CloudWatch retention for approval-gate logs. Approval logs are audit evidence — keep them longer than ordinary application logs."
  type        = number
  default     = 365
}

variable "kms_key_arn" {
  description = "Customer-managed KMS key ARN."
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags applied to every resource in this module."
  type        = map(string)
  default     = {}
}
