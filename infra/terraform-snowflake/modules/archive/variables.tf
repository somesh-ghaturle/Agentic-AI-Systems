variable "name_prefix" {
  description = "Prefix for the export stage name."
  type        = string
}

variable "database_name" {
  description = "Database holding the archive."
  type        = string
}

variable "schema_name" {
  description = "Schema holding the archive. AUDIT."
  type        = string
}

variable "archive_retention_days" {
  description = "Time Travel window on the archive table. Zero is defensible here and nowhere else in this tree: the rows are already a copy of an append-only source."
  type        = number
  default     = 1

  validation {
    condition     = var.archive_retention_days >= 0 && var.archive_retention_days <= 90
    error_message = "archive_retention_days must be between 0 and 90."
  }
}

variable "reader_roles" {
  description = "Roles granted SELECT on the archive, keyed by name."
  type        = map(string)
  default     = {}
}
