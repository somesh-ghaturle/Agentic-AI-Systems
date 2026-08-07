variable "name_prefix" {
  description = "Prefix for resource names, typically \"<project>-<env>\". Must yield a globally unique bucket name."
  type        = string
}

variable "kms_key_arn" {
  description = "Customer-managed KMS key ARN. Null uses SSE-S3 (AES256)."
  type        = string
  default     = null
}

variable "transition_ia_days" {
  description = "Days before traces move to STANDARD_IA."
  type        = number
  default     = 30
}

variable "transition_glacier_days" {
  description = "Days before traces move to GLACIER."
  type        = number
  default     = 90
}

variable "expiration_days" {
  description = "Days before traces are deleted. Null retains indefinitely. In a regulated environment this comes from your records policy, not from a default."
  type        = number
  default     = null
}

variable "noncurrent_version_expiration_days" {
  description = "Days before superseded object versions are purged."
  type        = number
  default     = 90
}

variable "object_lock_retention_days" {
  description = <<-EOT
    Enables S3 Object Lock in COMPLIANCE mode for this many days. Null disables it.

    Two things to know before setting this:
      - It must be decided at creation. S3 cannot enable Object Lock on an existing
        bucket, so changing this later forces bucket replacement.
      - COMPLIANCE mode cannot be shortened or overridden by anyone, including the root
        account, until the window elapses. That is the point in an audit context and a
        serious inconvenience outside one.
  EOT
  type        = number
  default     = null
}

variable "tags" {
  description = "Tags applied to every resource in this module."
  type        = map(string)
  default     = {}
}
