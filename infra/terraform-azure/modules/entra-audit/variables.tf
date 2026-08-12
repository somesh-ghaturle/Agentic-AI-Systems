variable "name_prefix" {
  description = <<-DESC
    Prefix identifying the stack whose service principals this watches.

    Used twice, and both matter. It names the diagnostic setting, which is tenant-scoped,
    so a collision here is a collision with another stack's setting rather than a
    same-environment error. It also filters the alert query to this stack's principals —
    without that filter, any unrelated application in the tenant would page whoever is on
    call for this one.
  DESC
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9-]{3,40}$", var.name_prefix))
    error_message = "name_prefix must be 3-40 characters of lowercase letters, digits, or hyphens."
  }
}

variable "resource_group_name" {
  description = "Resource group holding the alert rule. The diagnostic setting is tenant-scoped and ignores this; only the alert rule is a normal ARM resource."
  type        = string
}

variable "location" {
  description = "Region for the alert rule."
  type        = string
}

variable "log_analytics_workspace_id" {
  description = <<-DESC
    Workspace receiving Entra AuditLogs and evaluating the alert.

    Point this at the workspace of the environment whose incidents you actually respond
    to — in practice, prod. The Entra tenant is shared across environments, so these
    records are not per-environment the way FunctionAppLogs are; sending them to a dev
    workspace means the one alert that describes an open security boundary lands where
    nobody is looking.
  DESC
  type        = string
}

variable "action_group_id" {
  description = "Action group to notify. Reuse the environment's existing group rather than creating a parallel one, so this alert reaches the same people as every other."
  type        = string
}

variable "capture_service_principal_signins" {
  description = <<-DESC
    Also route ServicePrincipalSignInLogs.

    Off by default because the volume is substantial and nothing here alerts on it. Turn
    it on where the retention cost is acceptable: when the alert in this module fires,
    the immediately following question is what the principal did while the boundary was
    open, and that is answerable from this table or not at all.
  DESC
  type        = bool
  default     = false
}

variable "tags" {
  description = "Tags applied to the alert rule."
  type        = map(string)
  default     = {}
}
