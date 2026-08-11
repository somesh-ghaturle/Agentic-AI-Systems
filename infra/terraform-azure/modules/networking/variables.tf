variable "name_prefix" {
  description = "Prefix for resource names, e.g. agentic-dev."
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group to create. Everything else in this stack is placed inside it."
  type        = string
}

variable "location" {
  description = "Azure region."
  type        = string
}

variable "address_space" {
  description = "VNet address space."
  type        = string
  default     = "10.0.0.0/16"
}

variable "subnet_prefix" {
  description = <<-DESC
    Subnet for private endpoints and Function App VNet integration.

    Nothing joins it yet — the Consumption (Y1) plan cannot integrate with a VNet, so
    every private-endpoint variable in this stack stays open until prod moves to an
    Elastic Premium plan. See ARCHITECTURE.md § Remaining work.
  DESC
  type        = string
  default     = "10.0.1.0/24"
}

variable "tags" {
  description = "Tags applied to every resource in this module."
  type        = map(string)
  default     = {}
}
