output "diagnostic_setting_id" {
  description = "ID of the tenant-scoped Entra diagnostic setting. Its presence is the thing to verify after apply — if it is absent, the AuditLogs table stays empty and the alert below sits at zero while reading as healthy."
  value       = azurerm_monitor_aad_diagnostic_setting.audit.id
}

output "alert_rule_id" {
  description = "ID of the write-boundary alert rule."
  value       = azurerm_monitor_scheduled_query_rules_alert_v2.role_assignment_disabled.id
}

output "verification_query" {
  description = <<-DESC
    KQL to paste into the workspace to confirm this is wired, and to rehearse the alert.

    Run it after apply. It should return the seed row and nothing else. If it errors with
    an unknown-table error instead, AuditLogs is not flowing — the diagnostic setting did
    not take effect, and ingestion can lag the first apply by up to about 15 minutes.

    To rehearse properly: flip app_role_assignment_required to false on a throwaway app
    registration named with this stack's prefix, confirm the alert fires, then set it
    back. An alert nobody has ever seen fire is a hypothesis, not a control.
  DESC
  value       = <<-KQL
    AuditLogs
    | where TimeGenerated > ago(24h)
    | where OperationName has "service principal" or OperationName has "application"
    | mv-expand target = TargetResources
    | mv-expand changed = target.modifiedProperties
    | where tostring(changed.displayName) has "AppRoleAssignmentRequired"
    | project TimeGenerated, OperationName,
              principal = tostring(target.displayName),
              oldValue  = tostring(changed.oldValue),
              newValue  = tostring(changed.newValue)
  KQL
}
