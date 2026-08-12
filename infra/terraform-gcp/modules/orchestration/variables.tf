variable "project_id" {
  description = "GCP project."
  type        = string
}

variable "name_prefix" {
  description = "Prefix for resource names, typically \"<project>-<env>\". The workflow is named \"<name_prefix>-orchestrator\", and callers rely on that being deterministic to break the observability cycle — see envs/dev/main.tf."
  type        = string
}

variable "location" {
  description = "Region for the workflow. Workflows is regional; the callback endpoint it mints is too."
  type        = string
}

# --- identity --------------------------------------------------------------

variable "orchestrator_service_account_email" {
  description = <<-EOT
    Service account the workflow runs as.

    Also the principal named in the deny policy, which takes an email rather than a member
    string. Supply `emails`, not `members`, from modules/identity.
  EOT

  type = string

  validation {
    condition     = can(regex("@", var.orchestrator_service_account_email))
    error_message = "orchestrator_service_account_email must be a service account email, not a member string. Pass `emails`, not `members`, from modules/identity — the deny policy builds its own principal:// form from this value and a `serviceAccount:` prefix would produce a rule that matches nothing."
  }
}

variable "orchestrator_member" {
  description = "Orchestrator principal in `serviceAccount:...` form, for the allow-policy grants (log writing)."
  type        = string
}

variable "caller_members" {
  description = <<-EOT
    Principals granted roles/workflows.invoker — whoever starts executions.

    Not granted to any workload in this tree. The caller is an API gateway, a scheduler, or
    a person, and it lives outside these modules. Empty means the workflow exists and
    nothing can start it.
  EOT

  type    = map(string)
  default = {}
}

# --- wiring ----------------------------------------------------------------

variable "read_tool_urls" {
  description = <<-EOT
    Read tool URLs keyed by tool name. Must contain "retrieve" and "reason" — the workflow
    calls both by name, and a missing key fails the precondition in main.tf at plan time.

    Write tool URLs deliberately do not appear here. Pass modules/tools `read_tool_urls`,
    never `tool_urls_by_name`.
  EOT

  type = map(string)
}

variable "validator_url" {
  description = "Approval validator URL. The orchestrator's only reach into the write path: it can ask whether a proposal is valid, and it can ask for a human to be notified. It cannot resolve the result."
  type        = string
}

variable "trace_emitter_url" {
  description = "Trace emitter URL. Null fails a precondition rather than deploying a workflow whose records reach no metric — see the precondition in main.tf for why that failure mode is worth blocking at plan time."
  type        = string
  default     = null
}

# --- execution bounds ------------------------------------------------------

variable "max_steps" {
  description = "Step ceiling for the reason/retrieve loop. Exceeding it raises rather than returning a truncated answer: a run that silently stops short looks like a short answer."
  type        = number
  default     = 10

  validation {
    condition     = var.max_steps > 0 && var.max_steps <= 100
    error_message = "max_steps must be between 1 and 100. An agent loop without a ceiling is an agent spending money without a ceiling."
  }
}

variable "approval_timeout_seconds" {
  description = <<-EOT
    How long an execution waits on the approval callback before abandoning it.

    Workflows caps `events.await_callback` at 31536000s (one year), but the practical
    ceiling is patience: an execution suspended for a week still holds its state and still
    resolves if somebody clicks approve, by which point the context that justified the
    write is stale.
  EOT

  type    = number
  default = 3600

  validation {
    condition     = var.approval_timeout_seconds >= 60 && var.approval_timeout_seconds <= 604800
    error_message = "approval_timeout_seconds must be between 60 and 604800 (one week)."
  }
}

variable "call_log_level" {
  description = "LOG_ALL_CALLS, LOG_ERRORS_ONLY, or LOG_NONE. LOG_ALL_CALLS is verbose and is the difference between diagnosing a stuck execution in minutes and reconstructing it from traces."
  type        = string
  default     = "LOG_ALL_CALLS"

  validation {
    condition     = contains(["LOG_ALL_CALLS", "LOG_ERRORS_ONLY", "LOG_NONE"], var.call_log_level)
    error_message = "call_log_level must be LOG_ALL_CALLS, LOG_ERRORS_ONLY, or LOG_NONE."
  }
}

# --- lock 2 ----------------------------------------------------------------

variable "write_tool_service_names" {
  description = <<-EOT
    Cloud Run service names backing the write tools, from modules/tools
    `write_tool_service_names`.

    These are matched against `resource.name` in the deny policy's condition. An empty list
    skips the deny policy entirely, which is correct when no write tools exist and wrong in
    every other case — if you expected a deny policy and got none, check that the tools
    module actually has a tool classified `write`.
  EOT

  type    = list(string)
  default = []
}

variable "denied_invoke_permissions" {
  description = <<-EOT
    Permissions denied to the orchestrator on write tool services.

    Both entries matter. `run.googleapis.com/routes.invoke` is what `roles/run.invoker`
    actually confers on the underlying Cloud Run service, and it is the one that does the
    work. `cloudfunctions.googleapis.com/functions.invoke` covers the gen1-style path.

    Deny policies validate their permission strings at apply time, not at plan time, and a
    permission that is not supported for deny is rejected outright. A permission that is
    supported but wrong applies cleanly and denies nothing — see the note in main.tf about
    rehearsing this once before relying on it.
  EOT

  type = list(string)

  default = [
    "run.googleapis.com/routes.invoke",
    "cloudfunctions.googleapis.com/functions.invoke",
  ]

  validation {
    condition     = length(var.denied_invoke_permissions) > 0
    error_message = "denied_invoke_permissions cannot be empty. A deny rule with no permissions applies cleanly, appears in the console, and denies nothing."
  }
}

variable "labels" {
  description = "Labels applied to the workflow."
  type        = map(string)
  default     = {}
}
