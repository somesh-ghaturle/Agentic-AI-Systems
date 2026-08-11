variable "name_prefix" {
  description = "Prefix for identity names, e.g. agentic-dev."
  type        = string
}

variable "resource_group_name" {
  description = "Resource group holding the identities."
  type        = string
}

variable "location" {
  description = "Azure region."
  type        = string
}

variable "identities" {
  description = <<-DESC
    Logical identity names to create, one managed identity each. The environment root
    passes the platform identities plus one per tool, so that every workload gets its
    own principal and can be granted exactly what it needs — the same shape as one IAM
    role per Lambda on the AWS side.
  DESC
  type        = set(string)

  validation {
    condition     = length(var.identities) > 0
    error_message = "At least one identity is required; an empty set leaves every workload unauthenticated."
  }

  validation {
    condition     = alltrue([for i in var.identities : can(regex("^[a-z0-9-]+$", i))])
    error_message = "Identity names must be lowercase alphanumeric with hyphens — they become Azure resource names."
  }
}

variable "tags" {
  description = "Tags applied to every identity."
  type        = map(string)
  default     = {}
}
