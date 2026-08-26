variable "name_prefix" {
  description = "Prefix for the task name."
  type        = string
}

variable "database_name" {
  description = "Database holding the task."
  type        = string
}

variable "schema_name" {
  description = "Schema holding the task and the approval procedures it calls. APP."
  type        = string
}

variable "warehouse_name" {
  description = "Warehouse the task runs on. It resumes on every sweep, which is what makes sweep_interval_minutes a cost lever."
  type        = string
}

variable "sweep_interval_minutes" {
  description = "How often to look for approved-but-unclaimed proposals. Every sweep resumes a warehouse, so this trades approval latency directly against standing cost."
  type        = number
  default     = 5

  validation {
    condition     = var.sweep_interval_minutes >= 1 && var.sweep_interval_minutes <= 1440
    error_message = "sweep_interval_minutes must be between 1 and 1440."
  }
}

variable "sweep_batch_size" {
  description = "Maximum approvals claimed per sweep. Bounds how much one run can do, so a backlog drains predictably instead of in one long expensive statement."
  type        = number
  default     = 50
}

variable "task_started" {
  description = "Whether the task is running. False by default: a task that starts before its grants settle fails its first runs in a way that reads like a permissions bug."
  type        = bool
  default     = false
}

variable "task_timeout_ms" {
  description = "Hard ceiling on one sweep. Keep comfortably under the approval module's stale_claim_seconds so a killed sweep is reclaimed rather than blocking."
  type        = number
  default     = 120000
}

variable "suspend_after_failures" {
  description = "Consecutive failures before Snowflake suspends the task. Suspension is the desired outcome — a task failing every five minutes forever is a warehouse bill with no output."
  type        = number
  default     = 5
}

variable "task_owner_role" {
  description = "Role owning the task. Granted the executor role, never the other way round."
  type        = string
}

variable "executor_role" {
  description = "Role holding the claim grants the task needs."
  type        = string
}
