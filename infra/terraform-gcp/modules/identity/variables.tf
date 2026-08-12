variable "project_id" {
  description = "GCP project that owns these service accounts."
  type        = string
}

variable "name_prefix" {
  description = "Prefix for display names, typically \"<project>-<env>\"."
  type        = string
}

variable "identities" {
  description = <<-EOT
    Service account IDs to create, as a set.

    These become GCP `account_id` values verbatim, so they must already satisfy the API's
    naming rules: 6-30 characters, lowercase letters, digits and hyphens, starting with a
    letter. Tool names in this system may contain underscores, so callers normalize before
    passing them in rather than relying on this module to guess the intent.
  EOT

  type = set(string)

  validation {
    condition     = alltrue([for id in var.identities : can(regex("^[a-z][a-z0-9-]{5,29}$", id))])
    error_message = "Each identity must be 6-30 characters, start with a lowercase letter, and contain only lowercase letters, digits and hyphens. Underscores are not permitted — normalize tool names before passing them in."
  }
}
