variable "name_prefix" {
  description = "Prefix for resource names, e.g. agentic-dev."
  type        = string
}

variable "resource_group_name" {
  description = "Resource group for the approval gate."
  type        = string
}

variable "location" {
  description = "Azure region."
  type        = string
}

variable "tenant_id" {
  description = "Entra tenant ID, for the validator's and executor's Easy Auth issuer endpoints."
  type        = string

  validation {
    condition     = can(regex("^[0-9a-fA-F-]{36}$", var.tenant_id))
    error_message = "tenant_id must be a GUID. An empty string produces an issuer URL that validates nothing."
  }
}

# ---------------------------------------------------------------------------
# Who may call the gate
# ---------------------------------------------------------------------------

variable "orchestrator_principal_id" {
  description = "Object ID of the orchestrator's managed identity. Receives the app role permitting it to request validation and open an approval."
  type        = string
}

variable "approver_principal_ids" {
  description = <<-DESC
    Object IDs of the principals permitted to resolve an approval, keyed by a name you
    choose. Users or groups — a group is usually right, so that adding an approver is a
    directory change rather than a Terraform apply.

    An empty map means nobody can approve anything, and every gated action will sit until
    its window closes. That is a safe failure rather than a quiet one, but it is still a
    failure: set this before anyone depends on the environment.
  DESC
  type        = map(string)
  default     = {}
}

# ---------------------------------------------------------------------------
# Identities
# ---------------------------------------------------------------------------

variable "validator_identity" {
  description = "Managed identity for the validator, from modules/identity."
  type = object({
    id           = string
    principal_id = string
    client_id    = string
  })
}

variable "executor_identity" {
  description = <<-DESC
    Managed identity for the executor, from modules/identity.

    This principal is the one granted the invoke app role on write tools over in
    modules/tools. It is the single point through which any state-changing action passes,
    which is why it gets its own identity rather than sharing the validator's.
  DESC
  type = object({
    id           = string
    principal_id = string
    client_id    = string
  })
}

# ---------------------------------------------------------------------------
# Packages
# ---------------------------------------------------------------------------

variable "validator_package_path" {
  description = "Zip for the validator function. Built by src/build.sh."
  type        = string

  validation {
    condition     = fileexists(var.validator_package_path)
    error_message = "validator_package_path does not exist. Run src/build.sh before planning."
  }
}

variable "executor_package_path" {
  description = "Zip for the executor function. Built by src/build.sh."
  type        = string

  validation {
    condition     = fileexists(var.executor_package_path)
    error_message = "executor_package_path does not exist. Run src/build.sh before planning."
  }
}

variable "validator_environment" {
  description = "App settings for the validator, e.g. POLICY_MAX_REFUND_CENTS."
  type        = map(string)
  default     = {}
}

variable "executor_environment" {
  description = "App settings for the executor, e.g. STALE_CLAIM_SECONDS."
  type        = map(string)
  default     = {}
}

variable "common_environment" {
  description = "App settings applied to both functions."
  type        = map(string)
  default     = {}
}

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

variable "enable_continuous_backup" {
  description = <<-DESC
    Point-in-time restore on the approvals account. Off in dev, on in prod: this is the
    record of who authorized what, and losing it to a bad deploy is a compliance problem
    rather than an inconvenience.
  DESC
  type        = bool
  default     = false
}

variable "approval_record_ttl_seconds" {
  description = <<-DESC
    TTL for approval records. Null keeps them forever, which is the default because
    expiring an audit trail is a records-policy decision rather than a storage
    optimization. Set it deliberately or not at all.
  DESC
  type        = number
  default     = null
}

variable "cosmos_public_network_access_enabled" {
  description = "Whether the Cosmos account is reachable from the internet. Requires a private endpoint before it can be closed."
  type        = bool
  default     = true
}

# ---------------------------------------------------------------------------
# Messaging
# ---------------------------------------------------------------------------

variable "servicebus_sku" {
  description = <<-DESC
    Basic, Standard, or Premium. Topics require Standard or better. Premium is what
    supports private endpoints and customer-managed keys — the reason prod uses it,
    despite costing substantially more than Standard.
  DESC
  type        = string
  default     = "Standard"

  validation {
    condition     = contains(["Standard", "Premium"], var.servicebus_sku)
    error_message = "Must be Standard or Premium. Basic does not support topics, and this module needs one."
  }
}

variable "servicebus_capacity" {
  description = "Messaging units, Premium only. Ignored for Standard."
  type        = number
  default     = 1
}

variable "servicebus_local_auth_enabled" {
  description = "Whether SAS connection strings work. False in prod — every caller here uses managed identity."
  type        = bool
  default     = true
}

variable "servicebus_public_network_access_enabled" {
  description = "Whether the namespace is reachable from the internet. Requires Premium + a private endpoint before it can be closed."
  type        = bool
  default     = true
}

# ---------------------------------------------------------------------------
# Compute and storage
# ---------------------------------------------------------------------------

variable "service_plan_sku" {
  description = "App Service plan SKU for the validator and executor."
  type        = string
  default     = "Y1"
}

variable "python_version" {
  description = "Python runtime for the approval functions."
  type        = string
  default     = "3.12"
}

variable "storage_replication_type" {
  description = "Replication for the approval functions' storage account."
  type        = string
  default     = "LRS"
}

variable "storage_shared_access_key_enabled" {
  description = "Whether the storage account accepts shared keys. False in prod."
  type        = bool
  default     = true
}

variable "storage_public_network_access_enabled" {
  description = "Whether the storage account is internet-reachable. Requires a private endpoint before it can be closed."
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags applied to every resource in this module."
  type        = map(string)
  default     = {}
}
