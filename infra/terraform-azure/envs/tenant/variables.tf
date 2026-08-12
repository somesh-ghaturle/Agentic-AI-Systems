variable "subscription_id" {
  description = "Subscription billing the alert rule. The diagnostic setting is tenant-scoped and does not belong to it."
  type        = string

  validation {
    condition     = can(regex("^[0-9a-fA-F-]{36}$", var.subscription_id))
    error_message = "subscription_id must be a GUID."
  }
}

variable "name_prefix" {
  description = <<-DESC
    Prefix of the stack being watched — the same value prod computes for itself.

    Get it wrong and nothing errors. The diagnostic setting still routes AuditLogs, the
    alert rule still deploys, and the query matches nothing forever. Check it against
    prod's actual resource names before applying, not after.
  DESC
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9-]{3,40}$", var.name_prefix))
    error_message = "name_prefix must be 3-40 characters of lowercase letters, digits, or hyphens."
  }
}

variable "resource_group_name" {
  description = "Existing resource group for the alert rule. Use prod's — `terraform -chdir=../prod output -raw resource_group_name`. This root creates no resource group of its own."
  type        = string
}

variable "location" {
  description = "Region for the alert rule. Match prod's."
  type        = string
  default     = "eastus"
}

variable "log_analytics_workspace_id" {
  description = "From `terraform -chdir=../prod output -raw log_analytics_workspace_id`. Prod's, not dev's — this alert describes an open security boundary and belongs where someone is on call."
  type        = string
}

variable "action_group_id" {
  description = "From `terraform -chdir=../prod output -raw action_group_id`."
  type        = string
}

variable "capture_service_principal_signins" {
  description = "Also route ServicePrincipalSignInLogs. Higher volume and higher cost; the payoff is being able to answer what a principal did while the boundary was open."
  type        = bool
  default     = false
}

variable "tags" {
  description = "Tags applied to the alert rule."
  type        = map(string)
  default     = {}
}
