output "archive_table" {
  description = "Fully qualified archive table."
  value       = "${var.database_name}.${var.schema_name}.${snowflake_table.archived_traces.name}"
}

output "export_stage" {
  description = "Fully qualified export stage."
  value       = "${var.database_name}.${var.schema_name}.${snowflake_stage_internal.exports.name}"
}
