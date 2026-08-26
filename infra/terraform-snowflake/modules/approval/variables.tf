variable "database_name" {
  description = "Database holding the approval objects."
  type        = string
}

variable "schema_name" {
  description = "Schema holding the approvals table and its procedures. Must be a managed-access schema."
  type        = string
}

variable "stale_claim_seconds" {
  description = "How long a claim may sit in EXECUTING before another executor may reclaim it. Safe only because write tools are idempotent on the approval ID. Must exceed the write tool's own timeout plus its retries, or a slow-but-alive execution gets a second executor alongside it."
  type        = number
  default     = 900

  validation {
    condition     = var.stale_claim_seconds >= 60
    error_message = "stale_claim_seconds must be at least 60. Below that, a merely slow write tool is reclaimed while it is still running."
  }
}

variable "tool_owner_role" {
  description = "Role taking ownership of the approval procedures and holding the table privileges."
  type        = string
}

variable "orchestrator_role" {
  description = "Role granted USAGE on SUBMIT_PROPOSAL. It gets nothing else here."
  type        = string
}

variable "executor_role" {
  description = "Role granted USAGE on CLAIM_APPROVAL and RESOLVE_APPROVAL. Deliberately not granted APPROVE."
  type        = string
}

variable "auditor_role" {
  description = "Role granted SELECT on the approvals table."
  type        = string
}

variable "approver_roles" {
  description = "Human roles permitted to call APPROVE, keyed by name. Never include the orchestrator or executor role: a machine role that can approve its own proposal collapses the gate into a formality. An empty set fails closed — proposals accumulate as PENDING and nothing can claim them."
  type        = map(string)
  default     = {}
}
