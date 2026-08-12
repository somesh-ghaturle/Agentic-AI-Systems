output "diagnostic_setting_id" {
  description = "Tenant-scoped Entra diagnostic setting. If this is empty after apply, nothing is flowing and the alert is decorative."
  value       = module.entra_audit.diagnostic_setting_id
}

output "alert_rule_id" {
  description = "The write-boundary alert rule."
  value       = module.entra_audit.alert_rule_id
}

output "verification_query" {
  description = "KQL to paste into the workspace to confirm AuditLogs is flowing. Run it after apply; ingestion can lag the first apply by roughly 15 minutes."
  value       = module.entra_audit.verification_query
}
