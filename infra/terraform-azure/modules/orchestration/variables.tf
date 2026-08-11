variable "name_prefix" {
  description = "Prefix for resource names, e.g. agentic-dev."
  type        = string
}

variable "resource_group_name" {
  description = "Resource group holding the workflow."
  type        = string
}

variable "location" {
  description = "Azure region."
  type        = string
}

variable "orchestrator_identity" {
  description = <<-DESC
    Managed identity the workflow runs as, from modules/identity.

    This is the same principal modules/tools grants the invoke app role on read tools.
    The two must be the same identity or the workflow gets a 403 from every tool it
    calls — and because the grant would still exist and still look correct in the
    portal, that failure is easy to misread as a networking problem.
  DESC
  type = object({
    id           = string
    principal_id = string
    client_id    = string
  })
}

variable "tags" {
  description = "Tags applied to every resource in this module."
  type        = map(string)
  default     = {}
}
