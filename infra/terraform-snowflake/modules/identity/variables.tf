variable "name_prefix" {
  description = "Prefix for service user names, typically \"<PROJECT>_<ENV>\"."
  type        = string
}

variable "database_name" {
  description = "Database used as each service user's default namespace."
  type        = string
}

variable "warehouse_name" {
  description = "Warehouse each service user defaults to."
  type        = string
}

variable "service_users" {
  description = <<-EOT
    Service users to create, keyed by short name. Each carries a federated identity rather
    than a credential — see the module header for why that is the point rather than a
    detail.

    Exactly one of `aws_role_arn`, `azure`, `gcp_subject` or `oidc` must be set per user.
    The precondition on the resource enforces it, because the runtime failure is an opaque
    authentication error rather than anything that names the cause.
  EOT
  type = map(object({
    role           = string
    comment        = string
    default_schema = string
    workload_identity = object({
      aws_role_arn = optional(string)
      gcp_subject  = optional(string)
      azure = optional(object({
        issuer  = string
        subject = string
      }))
      oidc = optional(object({
        issuer        = string
        subject       = string
        audience_list = optional(list(string))
      }))
    })
  }))
  default = {}
}

variable "network_policy_name" {
  description = "Network policy attached to these users. Null attaches none."
  type        = string
  default     = null
}
