variable "resource_group_name" {
  type        = string
  description = "Name of the resource group to create"
}

variable "location" {
  type        = string
  description = "Azure region"
  default     = "eastus"
}

variable "name_prefix" {
  type        = string
  description = "Prefix for resources"
  default     = "agentic"
}

variable "address_space" {
  type        = string
  description = "VNet address space"
  default     = "10.0.0.0/16"
}

variable "subnet_prefix" {
  type        = string
  description = "Subnet address prefix"
  default     = "10.0.1.0/24"
}
