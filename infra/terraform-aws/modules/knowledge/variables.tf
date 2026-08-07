variable "name_prefix" {
  description = "Prefix for resource names. OpenSearch Serverless collection names are 3-32 chars, lowercase alphanumeric and hyphens."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9-]{1,22}$", var.name_prefix))
    error_message = "name_prefix must be lowercase alphanumeric/hyphens and short enough that \"<prefix>-knowledge\" stays within the 32-char collection name limit."
  }
}

variable "kms_key_arn" {
  description = "Customer-managed KMS key ARN. Null uses an AWS-owned key."
  type        = string
  default     = null
}

variable "allow_public_access" {
  description = "Allow reaching the collection from the public internet. Leave false for any corpus that may hold customer documents — set true only for a throwaway sandbox."
  type        = bool
  default     = false
}

variable "vpc_id" {
  description = "VPC for the collection endpoint. Required unless allow_public_access is true."
  type        = string
  default     = null
}

variable "subnet_ids" {
  description = "Subnets for the collection endpoint. Required unless allow_public_access is true."
  type        = list(string)
  default     = []
}

variable "security_group_ids" {
  description = "Security groups for the collection endpoint."
  type        = list(string)
  default     = []
}

variable "access_principal_arns" {
  description = "IAM role ARNs granted document and index access — typically the orchestrator and retrieval tool roles."
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Tags applied to every resource in this module."
  type        = map(string)
  default     = {}
}
