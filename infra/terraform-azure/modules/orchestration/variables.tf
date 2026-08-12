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

    This must be the same principal modules/tools granted the read-tool invoke role to.
    If it is not, every call the workflow makes returns 403 — and because the grant still
    exists and still looks correct in the portal, that failure is easy to misread as a
    networking problem.
  DESC
  type = object({
    id           = string
    principal_id = string
    client_id    = string
  })
}

# ---------------------------------------------------------------------------
# What the workflow calls
# ---------------------------------------------------------------------------

variable "read_tool_urls" {
  description = <<-DESC
    Read tool endpoints, keyed by tool name. Write tool URLs must never be passed here —
    the workflow is built from this map, so a write tool has no address to call even
    before Entra refuses it a token.
  DESC
  type        = map(string)

  validation {
    condition     = alltrue([for required in ["retrieve", "reason"] : contains(keys(var.read_tool_urls), required)])
    error_message = "read_tool_urls must contain both 'retrieve' and 'reason'. The workflow definition references them by name, so a missing one is a 404 at runtime rather than an error at plan."
  }
}

variable "tool_audiences" {
  description = <<-DESC
    Audience each tool's token must be minted for, keyed by tool name.

    Not optional even though Azure accepts an Http action without one: omitted, the
    platform requests a token for the ARM audience, which the tool's Easy Auth correctly
    refuses. That failure reads as a permissions problem and is not one.
  DESC
  type        = map(string)

  validation {
    condition     = alltrue([for required in ["retrieve", "reason"] : contains(keys(var.tool_audiences), required)])
    error_message = "tool_audiences must contain both 'retrieve' and 'reason'."
  }
}

variable "validator_url" {
  description = <<-DESC
    Validator endpoint. Called twice with different modes: `validate` for the
    deterministic pre-check, then `request_approval` as the webhook subscribe call that
    carries the callback URL.

    One endpoint rather than two because the two calls share all their argument handling
    and fingerprinting logic; splitting them invites the second to drift from the first,
    which is precisely the drift the fingerprint exists to catch.
  DESC
  type        = string
}

variable "validator_audience" {
  description = "Audience the workflow requests a token for when calling the validator."
  type        = string
}

variable "trace_emitter" {
  description = <<-DESC
    Where the workflow writes its own trace records.

    Required, not optional. A workflow's run history lands in a different table with a
    different shape from handler logs, so without this the loop-bound and daily-cost
    alerts match nothing — and an alert matching nothing is indistinguishable from a
    healthy system. Every terminal path in the definition writes one of these.
  DESC
  type = object({
    url      = string
    audience = string
  })
}

# ---------------------------------------------------------------------------
# Bounds
# ---------------------------------------------------------------------------

variable "max_steps" {
  description = <<-DESC
    Step budget. Exceeding it terminates the run as Failed — an agent that loops is an
    agent spending money, and a quiet stop returning a partial answer as though it were
    complete is worse than a visible failure.
  DESC
  type        = number
  default     = 8

  validation {
    condition     = var.max_steps >= 1 && var.max_steps <= 50
    error_message = "max_steps must be between 1 and 50. Above that the loop bound has stopped being a bound."
  }
}

variable "approval_timeout" {
  description = <<-DESC
    ISO 8601 duration the run stays suspended waiting for a human. PT24H in dev, PT4H in
    prod — a shorter production window is deliberate, because an approval nobody answered
    for four hours is already an incident.
  DESC
  type        = string
  default     = "PT24H"

  validation {
    condition     = can(regex("^P(T?[0-9]+[DHMS])+$", var.approval_timeout))
    error_message = "approval_timeout must be an ISO 8601 duration, e.g. PT4H."
  }
}

variable "tags" {
  description = "Tags applied to every resource in this module."
  type        = map(string)
  default     = {}
}
