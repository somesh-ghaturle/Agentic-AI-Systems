output "search_service_name" {
  description = "Fully qualified Cortex Search service."
  value       = "${var.database_name}.${var.schema_name}.${snowflake_cortex_search_service.main.name}"
}

output "documents_table" {
  description = "Fully qualified documents table the index is built over."
  value       = "${var.database_name}.${var.schema_name}.${snowflake_table.documents.name}"
}
