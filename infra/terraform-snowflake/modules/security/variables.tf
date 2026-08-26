variable "name_prefix" {
  description = "Prefix for role and policy names, typically \"<PROJECT>_<ENV>\"."
  type        = string
}

variable "database_name" {
  description = "Database the roles are granted USAGE on."
  type        = string
}

variable "audit_schema" {
  description = "Schema holding the masking policies. AUDIT rather than APP because a masking policy is governance, and governance objects belong with the audit trail."
  type        = string
}

variable "warehouse_name" {
  description = "Warehouse every role is granted USAGE on. Without it a role holding every table grant still cannot run a query."
  type        = string
}

variable "allowed_ip_list" {
  description = "CIDRs permitted to authenticate as the service users. Empty creates no policy at all, which is the honest default — an empty allow-list in Snowflake blocks everything, and a policy that locks out an operator mid-incident is a policy that gets disabled permanently."
  type        = list(string)
  default     = []
}

variable "blocked_ip_list" {
  description = "CIDRs denied even if they appear in allowed_ip_list. Snowflake evaluates blocked first."
  type        = list(string)
  default     = []
}

variable "create_masking_policies" {
  description = "Create the column masking policies. On in every environment that holds real data; the policy is free and only costs on read."
  type        = bool
  default     = true
}
