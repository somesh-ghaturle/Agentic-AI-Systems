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

variable "account_replication_type" {
  type        = string
  description = "Storage account replication type"
  default     = "LRS"
}

variable "transition_cool_days" {
  type        = number
  description = "Days before transitioning to Cool tier"
  default     = 7
}

variable "transition_archive_days" {
  type        = number
  description = "Days before transitioning to Archive tier"
  default     = 30
}

variable "expiration_days" {
  type        = number
  description = "Days before deleting the blob"
  default     = 90
}

variable "tags" {
  type        = map(string)
  description = "Tags to apply to resources"
  default     = {}
}
