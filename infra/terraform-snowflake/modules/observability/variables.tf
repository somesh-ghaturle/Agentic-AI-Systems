variable "name_prefix" {
  description = "Prefix for the event table name."
  type        = string
}

variable "database_name" {
  description = "Database holding the traces and the event table."
  type        = string
}

variable "schema_name" {
  description = "Schema holding the traces and the event table. AUDIT."
  type        = string
}

variable "trace_writer_roles" {
  description = "Roles granted INSERT on the trace table, keyed by name. INSERT only — a trace that can be revised is not evidence."
  type        = map(string)
  default     = {}
}

variable "trace_reader_roles" {
  description = "Roles granted SELECT on the trace table, keyed by name."
  type        = map(string)
  default     = {}
}
