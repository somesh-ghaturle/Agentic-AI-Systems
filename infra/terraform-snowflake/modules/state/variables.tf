variable "name_prefix" {
  description = "Prefix for object names, typically \"<PROJECT>_<ENV>\". Uppercase by Snowflake convention — an unquoted identifier is folded to uppercase anyway, and mixing the two produces objects that must be quoted forever after."
  type        = string

  validation {
    condition     = can(regex("^[A-Z][A-Z0-9_]*$", var.name_prefix))
    error_message = "name_prefix must be an unquoted-safe uppercase identifier: A-Z, 0-9 and underscore, starting with a letter."
  }
}

variable "database_name" {
  description = "Name of the database holding the whole stack."
  type        = string
}

variable "data_retention_time_in_days" {
  description = "Time Travel window. 1 in dev; the audit trail is what makes a longer window worth paying for in prod. Standard edition caps this at 1 — above that needs Enterprise."
  type        = number
  default     = 1

  validation {
    condition     = var.data_retention_time_in_days >= 0 && var.data_retention_time_in_days <= 90
    error_message = "data_retention_time_in_days must be between 0 and 90."
  }
}

variable "warehouse_size" {
  description = "Warehouse size. XSMALL is the right default: agent workloads are many small queries, and a larger warehouse makes each one cost more without making it finish sooner."
  type        = string
  default     = "XSMALL"
}

variable "auto_suspend_seconds" {
  description = "Idle seconds before the warehouse suspends. 60 rather than Snowflake's 600 default — ten idle minutes after every short agent run is the largest avoidable cost in this stack."
  type        = number
  default     = 60

  validation {
    condition     = var.auto_suspend_seconds >= 60
    error_message = "auto_suspend_seconds must be at least 60. Below that, warehouse resume churn costs more than the idle time it saves."
  }
}

variable "statement_timeout_in_seconds" {
  description = "Hard ceiling on any single statement. A runaway query in an agent loop is a bill, not an outage."
  type        = number
  default     = 300
}

variable "statement_queued_timeout_in_seconds" {
  description = "How long a statement may queue before it is abandoned. Bounds the pile-up when an agent retries faster than the warehouse drains."
  type        = number
  default     = 120
}

variable "max_cluster_count" {
  description = "Multi-cluster ceiling. 1 outside prod: multi-cluster scales concurrency, and one agent under test has none."
  type        = number
  default     = 1
}
