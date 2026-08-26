output "traces_table" {
  description = "Fully qualified trace table."
  value       = "${var.database_name}.${var.schema_name}.${snowflake_table.traces.name}"
}

output "event_table" {
  description = "Fully qualified event table. Created through snowflake_execute — see the module header on what that costs in drift detection."
  value       = local.event_table
}
