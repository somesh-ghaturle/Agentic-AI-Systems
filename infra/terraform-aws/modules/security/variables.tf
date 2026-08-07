variable "name_prefix" {
  description = "Prefix for resource names, typically \"<project>-<env>\"."
  type        = string
}

variable "key_deletion_window_days" {
  description = "KMS deletion window. The maximum is 30; use it in prod — a key deleted in error takes its data with it."
  type        = number
  default     = 30

  validation {
    condition     = var.key_deletion_window_days >= 7 && var.key_deletion_window_days <= 30
    error_message = "key_deletion_window_days must be between 7 and 30."
  }
}

variable "create_guardrail" {
  description = "Create a Bedrock guardrail. Only applicable if the model layer runs on Bedrock; leave false when calling a vendor API directly."
  type        = bool
  default     = false
}

variable "content_filters" {
  description = "Bedrock content filter strengths by category."
  type = list(object({
    type            = string
    input_strength  = string
    output_strength = string
  }))
  default = [
    { type = "PROMPT_ATTACK", input_strength = "HIGH", output_strength = "NONE" },
    { type = "MISCONDUCT", input_strength = "HIGH", output_strength = "HIGH" },
  ]
}

variable "pii_entities" {
  description = <<-EOT
    PII entities to mask or block at the model boundary.

    A backstop, not the primary control. PRODUCTION-PRINCIPLES.md is explicit that masking
    happens before data leaves your boundary — this catches what upstream masking missed,
    including PII arriving through the indirect paths teams forget: stack traces, error
    messages, tool outputs, and retrieved documents.
  EOT
  type = list(object({
    type   = string
    action = string
  }))
  default = []
}

variable "blocked_input_message" {
  description = "Shown when input is blocked."
  type        = string
  default     = "This request could not be processed."
}

variable "blocked_output_message" {
  description = "Shown when output is blocked."
  type        = string
  default     = "This response could not be returned."
}

variable "tags" {
  description = "Tags applied to every resource in this module."
  type        = map(string)
  default     = {}
}
