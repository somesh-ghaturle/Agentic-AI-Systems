variable "resource_group_name" {
  type        = string
  description = "Name of the resource group"
}

variable "location" {
  type        = string
  description = "Azure region"
}

variable "name_prefix" {
  type        = string
  description = "Prefix for naming resources"
}

variable "tags" {
  type        = map(string)
  description = "Tags to apply to resources"
  default     = {}
}

variable "enable_continuous_backup" {
  description = <<-DESC
    Point-in-time restore on the execution-state account. Off by default and on in prod.
    It is a one-way door: Cosmos continuous backup cannot be disabled once enabled, so
    undoing it means recreating the account. That is why staging leaves it off.
  DESC
  type        = bool
  default     = false
}

variable "continuous_backup_tier" {
  description = "Restore window when continuous backup is on. Continuous7Days is free; Continuous30Days is billed."
  type        = string
  default     = "Continuous7Days"

  validation {
    condition     = contains(["Continuous7Days", "Continuous30Days"], var.continuous_backup_tier)
    error_message = "continuous_backup_tier must be Continuous7Days or Continuous30Days."
  }
}

variable "public_network_access_enabled" {
  description = "Whether the account accepts connections from outside a virtual network. Matches the approvals account's input of the same meaning."
  type        = bool
  default     = true
}
