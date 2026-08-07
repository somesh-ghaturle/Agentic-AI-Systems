variable "name_prefix" {
  description = "Prefix for resource names, typically \"<project>-<env>\"."
  type        = string
}

variable "billing_mode" {
  description = "PAY_PER_REQUEST until traffic shape is known; PROVISIONED once it is steady."
  type        = string
  default     = "PAY_PER_REQUEST"

  validation {
    condition     = contains(["PAY_PER_REQUEST", "PROVISIONED"], var.billing_mode)
    error_message = "billing_mode must be PAY_PER_REQUEST or PROVISIONED."
  }
}

variable "point_in_time_recovery" {
  description = "Enable PITR. Recommended in prod: protects against corrupted in-flight state, which resuming cannot fix."
  type        = bool
  default     = true
}

variable "kms_key_arn" {
  description = "Customer-managed KMS key ARN for encryption at rest. Null uses the AWS-owned key."
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags applied to every resource in this module."
  type        = map(string)
  default     = {}
}
