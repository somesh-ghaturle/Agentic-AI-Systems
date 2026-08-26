output "sweeper_task_name" {
  description = "Fully qualified approval sweeper task."
  value       = "${var.database_name}.${var.schema_name}.${snowflake_task.approval_sweeper.name}"
}

output "sweeper_started" {
  description = "Whether the sweeper is running. False leaves approvals unclaimed — deliberate for a first apply."
  value       = var.task_started
}
