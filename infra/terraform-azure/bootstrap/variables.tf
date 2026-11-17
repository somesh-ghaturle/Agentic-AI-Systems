variable "subscription_id" {
  description = "Subscription that owns the state storage account."
  type        = string
}

variable "project" {
  description = "Project name. Use the same value the environment roots use."
  type        = string
  default     = "agentic"
}

variable "location" {
  description = "Azure region for the state resource group and storage account."
  type        = string
  default     = "eastus"
}

variable "storage_account_suffix" {
  description = "Lowercase letters and digits appended to the storage account name to make it globally unique."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9]{3,8}$", var.storage_account_suffix))
    error_message = "storage_account_suffix must be 3 to 8 lowercase letters or digits."
  }
}

variable "account_replication_type" {
  description = "Replication for the state account. GRS keeps a copy in the paired region."
  type        = string
  default     = "GRS"
}

variable "soft_delete_retention_days" {
  description = "Days a deleted state blob or the container remains recoverable."
  type        = number
  default     = 30

  validation {
    condition     = var.soft_delete_retention_days >= 7 && var.soft_delete_retention_days <= 365
    error_message = "soft_delete_retention_days must be between 7 and 365."
  }
}
