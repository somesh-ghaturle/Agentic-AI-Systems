variable "database_name" {
  description = "Database holding the tool procedures."
  type        = string
}

variable "schema_name" {
  description = "Schema holding the tool procedures. Must be a managed-access schema — see modules/state for why that is load-bearing rather than tidy."
  type        = string
}

variable "read_tools" {
  description = <<-EOT
    Read tools, keyed by procedure name. Ungated by design: THREAT-MODEL.md names the
    ungated read path as the architecture's largest genuine gap, and the answer is to
    scope what these return, not to gate them.
  EOT
  type = map(object({
    return_type = string
    definition  = string
    arguments = list(object({
      name = string
      type = string
    }))
  }))
  default = {}
}

variable "write_tools" {
  description = <<-EOT
    Write tools, keyed by procedure name. USAGE on each goes to the executor role and to
    nothing else — that grant is the write boundary on this cloud.

    Every write tool must be idempotent on the approval ID it is passed. The approval
    gate's stale-claim recovery re-invokes a write whose executor died mid-flight, and
    that recovery is safe only because a re-invocation with the same key returns the
    original result rather than acting twice.
  EOT
  type = map(object({
    return_type = string
    definition  = string
    arguments = list(object({
      name = string
      type = string
    }))
  }))
  default = {}
}

variable "write_table_names" {
  description = "Fully qualified tables the write procedures modify. Granted to the tool owner alone — a caller role holding INSERT here would make the procedure boundary decoration."
  type        = set(string)
  default     = []
}

variable "tool_owner_role" {
  description = "Role that owns every procedure and holds the table privileges. Granted to no user."
  type        = string
}

variable "orchestrator_role" {
  description = "Role granted USAGE on read procedures."
  type        = string
}

variable "executor_role" {
  description = "Role granted USAGE on write procedures. The only one."
  type        = string
}
