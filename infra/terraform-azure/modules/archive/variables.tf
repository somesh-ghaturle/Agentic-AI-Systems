variable "name_prefix" {
  description = "Prefix for resource names, e.g. agentic-dev."
  type        = string
}

variable "resource_group_name" {
  description = "Resource group holding the archive."
  type        = string
}

variable "location" {
  description = "Azure region."
  type        = string
}

variable "account_replication_type" {
  description = "Replication for the archive account. LRS in dev, GRS in prod — this is the evidence trail."
  type        = string
  default     = "LRS"
}

variable "shared_access_key_enabled" {
  description = "Whether the account accepts its shared keys. False in prod; every writer authenticates as itself."
  type        = bool
  default     = true
}

variable "soft_delete_retention_days" {
  description = "Days a deleted blob or container remains recoverable. Distinct from immutability — this covers accidents, immutability covers intent."
  type        = number
  default     = 30

  validation {
    condition     = var.soft_delete_retention_days >= 1 && var.soft_delete_retention_days <= 365
    error_message = "soft_delete_retention_days must be between 1 and 365."
  }
}

variable "immutability_period_days" {
  description = <<-DESC
    Days a trace blob cannot be deleted or overwritten by anyone, including the
    subscription owner. Null creates no immutability policy at all, which is the dev
    default — a container nobody can empty is a dev environment nobody can tear down.

    Set this in any environment where the traces are audit evidence rather than debug
    output.
  DESC
  type        = number
  default     = null

  validation {
    condition     = var.immutability_period_days == null || try(var.immutability_period_days >= 1, false)
    error_message = "immutability_period_days must be null or at least 1."
  }
}

variable "lock_immutability_policy" {
  description = <<-DESC
    Lock the immutability policy. **This cannot be undone.**

    Unlocked, the policy can be deleted and its retention shortened — which means it
    protects against accident but not against intent, and an unlocked WORM policy is not
    a compliance control. Locked, the retention period can only be extended, and the
    container and storage account cannot be destroyed until every blob has aged out.

    That includes by `terraform destroy`. Set this true in prod knowingly; a locked
    seven-year policy means a seven-year resource group.
  DESC
  type        = bool
  default     = false
}

variable "transition_cool_days" {
  description = "Days before tiering to Cool."
  type        = number
  default     = 7
}

variable "transition_archive_days" {
  description = "Days before tiering to Archive."
  type        = number
  default     = 30
}

variable "expiration_days" {
  description = "Days before deletion. Cannot take effect earlier than immutability_period_days, whatever it is set to."
  type        = number
  default     = 90

  validation {
    condition     = var.expiration_days > var.transition_archive_days
    error_message = "expiration_days must be greater than transition_archive_days, or blobs are deleted before they ever reach the Archive tier and the tiering is decorative."
  }
}

variable "tags" {
  description = "Tags applied to every resource in this module."
  type        = map(string)
  default     = {}
}
