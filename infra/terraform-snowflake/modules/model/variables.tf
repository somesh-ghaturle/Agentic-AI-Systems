variable "database_name" {
  description = "Database holding the guarded entry point."
  type        = string
}

variable "schema_name" {
  description = "Schema holding the guarded entry point. TOOLS, so it inherits managed access."
  type        = string
}

variable "model_name" {
  description = "Cortex model identifier. Claude here, matching the AWS and GCP trees; see docs/DECISION-LOGS/0002-azure-openai-vs-claude.md for why Azure differs."
  type        = string
  default     = "claude-sonnet-4-5"
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
