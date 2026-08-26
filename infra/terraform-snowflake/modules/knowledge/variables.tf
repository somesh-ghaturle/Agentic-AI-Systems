variable "name_prefix" {
  description = "Prefix for the search service name."
  type        = string
}

variable "database_name" {
  description = "Database holding the documents table and search service."
  type        = string
}

variable "schema_name" {
  description = "Schema holding the documents table and search service."
  type        = string
}

variable "warehouse_name" {
  description = "Warehouse the search service refreshes on. It resumes on every refresh, so this and target_lag together set the standing cost of retrieval."
  type        = string
}

variable "target_lag" {
  description = "Declared freshness contract, e.g. \"1 hour\". Snowflake is responsible for meeting it. Minutes here means a warehouse resuming every few minutes forever, whether or not anyone queries."
  type        = string
  default     = "1 hour"
}

variable "embedding_model" {
  description = "Embedding model backing the index. Changing it rebuilds the whole index."
  type        = string
  default     = "snowflake-arctic-embed-l-v2.0"
}

variable "orchestrator_role" {
  description = "Role granted USAGE on the search service. Retrieval is ungated by design."
  type        = string
}

variable "document_reader_roles" {
  description = "Roles granted SELECT on the documents table itself, keyed by name."
  type        = map(string)
  default     = {}
}
