variable "name_prefix" {
  description = "Prefix for resource names, e.g. agentic-dev."
  type        = string
}

variable "resource_group_name" {
  description = "Resource group holding the workspace."
  type        = string
}

variable "location" {
  description = "Azure region."
  type        = string
}

variable "log_retention_days" {
  description = <<-DESC
    Days logs are kept. 30 in dev; prod keeps traces long enough to answer "who approved
    this and on what evidence" after the fact, which is the whole reason the trace
    records exist.
  DESC
  type        = number
  default     = 30

  validation {
    condition     = var.log_retention_days >= 30 && var.log_retention_days <= 730
    error_message = "Log Analytics retention must be between 30 and 730 days."
  }
}

variable "tags" {
  description = "Tags applied to every resource in this module."
  type        = map(string)
  default     = {}
}
