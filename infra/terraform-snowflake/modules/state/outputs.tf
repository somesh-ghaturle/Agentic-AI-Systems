output "database_name" {
  description = "Database holding the whole stack."
  value       = snowflake_database.main.name
}

output "app_schema" {
  description = "Schema holding execution state and approval records."
  value       = snowflake_schema.app.name
}

output "tools_schema" {
  description = "Schema holding the read and write tool procedures. The write boundary is drawn inside it."
  value       = snowflake_schema.tools.name
}

output "audit_schema" {
  description = "Schema holding traces and the archive."
  value       = snowflake_schema.audit.name
}

output "warehouse_name" {
  description = "Warehouse every handler runs on."
  value       = snowflake_warehouse.main.name
}

output "execution_state_table" {
  description = "Fully qualified execution-state table."
  value       = "${snowflake_database.main.name}.${snowflake_schema.app.name}.${snowflake_hybrid_table.execution_state.name}"
}

output "cost_monitor_name" {
  description = "Resource monitor bounding the warehouse's credit spend. Null when cost_monitor_credit_quota is null — no monitor exists to name."
  value       = try(snowflake_resource_monitor.warehouse_cost[0].name, null)
}
