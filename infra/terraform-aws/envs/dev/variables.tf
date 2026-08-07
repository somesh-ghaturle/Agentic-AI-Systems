variable "project" {
  description = "Project name. Combined with the environment to prefix every resource."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9-]{1,17}$", var.project))
    error_message = "project must be lowercase alphanumeric/hyphens and at most 17 chars, so \"<project>-dev-knowledge\" stays within the 32-char OpenSearch collection name limit."
  }
}

variable "region" {
  description = "AWS region."
  type        = string
  default     = "us-east-1"
}

variable "tools" {
  description = <<-EOT
    Tool definitions. See modules/tools/variables.tf for the full contract.

    The `access` field decides who may invoke each function — "read" means the
    orchestrator calls it directly, "write" means only the approval executor can. Classify
    honestly: a tool marked read that mutates state defeats the split, and no amount of
    Terraform can detect that.
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
}

variable "approval_validator" {
  description = "Validator function — deterministic ownership, permission, and limit checks that run before a human sees a proposal."

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

variable "alarm_topic_arns" {
  description = "SNS topics notified when an alarm fires."
  type        = list(string)
  default     = []
}
