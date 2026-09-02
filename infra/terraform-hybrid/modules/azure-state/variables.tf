variable "resource_group_name" {
  description = "Existing resource group for the state account."
  type        = string
}

variable "location" {
  description = "Azure region."
  type        = string
}

variable "name_prefix" {
  description = "Lowercase prefix used for globally unique names."
  type        = string
}

variable "enable_resources" {
  description = "Create cloud resources only when explicitly enabled."
  type        = bool
  default     = false
}
