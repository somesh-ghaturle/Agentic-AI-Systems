variable "database_name" {
  description = "Database holding the guarded entry point."
  type        = string
}

variable "schema_name" {
  description = "Schema holding the guarded entry point. TOOLS, so it inherits managed access."
  type        = string
}

variable "model_name" {
  description = "Cortex model identifier. Claude here, matching the AWS and GCP trees; see docs/DECISION-LOGS/0002-azure-openai-vs-claude.md for why Azure differs. Held one generation behind AWS and GCP on purpose — see the comment below."
  type        = string

  # Deliberately not `claude-opus-5`, which the AWS and GCP trees moved to in task 46.
  #
  # Checked against Snowflake's model availability documentation on 2026-09-03: Cortex does list
  # `claude-opus-5`, so "Cortex does not offer it" is not the reason. The reason is how it offers
  # it — opus-5 is reachable only through cross-region inference, with no native region, while
  # `claude-sonnet-4-5` runs natively.
  #
  # Cross-region inference transmits the prompt and the response out of the account's home region
  # for the duration of the call. Nothing is stored there, and the transport is encrypted and
  # mutually authenticated, but the payload still leaves. Turning it on is an ACCOUNTADMIN-only
  # `ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION`, and it defaults to DISABLED on accounts
  # created before 2026-03-09.
  #
  # So bumping this default would hand every operator a tree that either fails on a parameter
  # they never set, or works because their account already permits inference payloads to leave
  # their region — a data-residency decision made for them, in a default, by a repository whose
  # subject is not making decisions like that for people. A newer model does not outrank that.
  #
  # Revisit when opus-5 gains a native Cortex region. Then this is an ordinary version bump.
  default = "claude-sonnet-4-5"
}

variable "temperature" {
  description = "Sampling temperature for the guarded entry point."
  type        = number
  default     = 0

  validation {
    condition     = var.temperature >= 0 && var.temperature <= 1
    error_message = "temperature must be between 0 and 1."
  }
}

variable "max_tokens" {
  description = "Output ceiling. A bound on cost per call as much as on response length."
  type        = number
  default     = 4096
}

variable "tool_owner_role" {
  description = "Role holding SNOWFLAKE.CORTEX_USER and owning the wrapper. Granted to no user."
  type        = string
}

variable "orchestrator_role" {
  description = "Role granted USAGE on the wrapper. Must NOT be granted SNOWFLAKE.CORTEX_USER — that is the grant that makes the guard bypassable."
  type        = string
}
