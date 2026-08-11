variable "name_prefix" {
  description = "Prefix for resource names, e.g. agentic-dev."
  type        = string
}

variable "resource_group_name" {
  description = "Resource group holding the vault."
  type        = string
}

variable "location" {
  description = "Azure region."
  type        = string
}

variable "tenant_id" {
  description = "Entra tenant the vault authenticates against."
  type        = string

  validation {
    condition     = can(regex("^[0-9a-fA-F-]{36}$", var.tenant_id))
    error_message = "tenant_id must be a GUID. The previous default of \"\" produced a vault bound to no tenant."
  }
}

variable "sku_name" {
  description = "standard or premium. Premium buys HSM-backed keys, which nothing here uses yet."
  type        = string
  default     = "standard"

  validation {
    condition     = contains(["standard", "premium"], var.sku_name)
    error_message = "sku_name must be standard or premium."
  }
}

variable "secret_reader_principal_ids" {
  description = <<-DESC
    Map of logical name to principal object ID, each granted "Key Vault Secrets User".

    A map rather than a list so that Terraform keys the assignments by name: adding or
    removing one workload does not re-index and recreate the others, which is what a
    list of principal IDs does the first time the order changes.

    Read only. Nothing in this system writes a secret at runtime — secrets are placed by
    an operator or by the pipeline, never by a handler.
  DESC
  type        = map(string)
  default     = {}
}

variable "purge_protection_enabled" {
  description = <<-DESC
    Once true, this cannot be set back to false, and the vault cannot be purged before
    its retention window elapses. That irreversibility is the point — it is what stops a
    deleted vault from taking the audit material with it. Prod: true.
  DESC
  type        = bool
  default     = true
}

variable "soft_delete_retention_days" {
  description = "Days a deleted vault or secret remains recoverable. 7 is the floor, 90 the ceiling."
  type        = number
  default     = 90

  validation {
    condition     = var.soft_delete_retention_days >= 7 && var.soft_delete_retention_days <= 90
    error_message = "soft_delete_retention_days must be between 7 and 90."
  }
}

variable "public_network_access_enabled" {
  description = <<-DESC
    Whether the vault is reachable from the internet. Setting this false switches the
    network ACL to deny-by-default and requires a private endpoint, or Terraform itself
    loses the data plane and secret writes fail mid-apply.
  DESC
  type        = bool
  default     = true
}

variable "create_model_key_secret" {
  description = "Create a secret holding the model API key. Unnecessary when the model layer authenticates by managed identity."
  type        = bool
  default     = false
}

variable "model_key_secret_name" {
  description = "Name of the model API key secret."
  type        = string
  default     = "model-api-key"
}

variable "model_key_secret_value" {
  description = "Value of the model API key. Pass via a protected tfvars file or TF_VAR_, never in source."
  type        = string
  default     = ""
  sensitive   = true
}

variable "tags" {
  description = "Tags applied to every resource in this module."
  type        = map(string)
  default     = {}
}
