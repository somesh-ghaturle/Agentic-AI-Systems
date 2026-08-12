variable "name_prefix" {
  description = "Prefix for resource names, e.g. agentic-dev."
  type        = string
}

variable "resource_group_name" {
  description = "Resource group holding the workspace and alerts."
  type        = string
}

variable "location" {
  description = "Azure region."
  type        = string
}

variable "tenant_id" {
  description = "Entra tenant ID, for the trace emitter's Easy Auth issuer endpoint."
  type        = string

  validation {
    condition     = can(regex("^[0-9a-fA-F-]{36}$", var.tenant_id))
    error_message = "tenant_id must be a GUID."
  }
}

variable "log_retention_days" {
  description = "Days logs are kept. 30 is the floor Log Analytics accepts; prod keeps traces long enough to answer questions raised months later."
  type        = number
  default     = 30

  validation {
    condition     = var.log_retention_days >= 30 && var.log_retention_days <= 730
    error_message = "Log Analytics retention must be between 30 and 730 days."
  }
}

# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

variable "function_app_ids" {
  description = <<-DESC
    Every Function App whose logs must reach the workspace, keyed by name.

    This must be complete. Function App logs do not reach Log Analytics without an
    explicit diagnostic setting, so an app missing from this map drops out of every alert
    query silently — nothing errors, the alert simply never fires for that component.
  DESC
  type        = map(string)
  default     = {}
}

variable "logic_app_id" {
  description = <<-DESC
    Resource ID of the orchestrator workflow, for its diagnostic setting and failure
    alert.

    Pass this as a constructed string from the environment root rather than reading it
    off the orchestration module. The workflow needs the trace emitter's URL, and the
    emitter lives here, so reading the ID back would form
    `orchestration → observability → orchestration`. ARM resource IDs are deterministic
    from the subscription, resource group, and name, so the value is known before the
    resource exists — the same cycle-break the AWS tree uses for its state machine ARN.
  DESC
  type        = string
  default     = null
}

# ---------------------------------------------------------------------------
# Trace emitter
# ---------------------------------------------------------------------------

variable "trace_emitter" {
  description = <<-DESC
    The function the orchestrator calls to write its own trace records. Null skips it
    entirely — and leaves the loop-bound and daily-cost alerts matching nothing, because
    a workflow's run history lands in a different table with a different shape.

    That failure is silent and looks exactly like health, which is why this is called out
    here rather than left to be discovered.
  DESC

  type = object({
    identity = object({
      id           = string
      principal_id = string
      client_id    = string
    })
    package_path              = string
    orchestrator_principal_id = string
  })

  default = null

  validation {
    condition     = var.trace_emitter == null || try(fileexists(var.trace_emitter.package_path), false)
    error_message = "trace_emitter.package_path does not exist. The zip is read to compute its deployment hash, so it must be built before planning."
  }
}

variable "service_plan_sku" {
  description = "App Service plan SKU for the trace emitter."
  type        = string
  default     = "Y1"
}

variable "python_version" {
  description = "Python runtime for the trace emitter."
  type        = string
  default     = "3.12"
}

variable "storage_replication_type" {
  description = "Replication for the trace emitter's storage account."
  type        = string
  default     = "LRS"
}

# ---------------------------------------------------------------------------
# Alerting
# ---------------------------------------------------------------------------

variable "alert_email_receivers" {
  description = <<-DESC
    Map of receiver name to email address. An empty map means every alert below fires
    into the void — the rules evaluate, the portal shows them firing, and nobody is told.
    Set this before anyone depends on the environment.
  DESC
  type        = map(string)
  default     = {}
}

variable "alert_webhook_receivers" {
  description = "Map of receiver name to webhook URI, for routing alerts into an incident tool."
  type        = map(string)
  default     = {}
}

variable "daily_cost_threshold_usd" {
  description = <<-DESC
    Daily spend, in USD, above which the cost alert fires. Null disables it.

    In dev this is a runaway-loop detector rather than a budget, so it belongs low. The
    query sums `cost_usd` from terminal trace records only — handlers emitting it per
    step will multiply-count and trip this spuriously.
  DESC
  type        = number
  default     = null
}

variable "schema_failure_threshold" {
  description = "Schema validation failures in a 5-minute window above which the alert fires. Null disables it."
  type        = number
  default     = null
}

variable "execution_failure_threshold" {
  description = "Failed orchestrator runs in a 15-minute window above which the alert fires."
  type        = number
  default     = 0
}

variable "tags" {
  description = "Tags applied to every resource in this module."
  type        = map(string)
  default     = {}
}
