# Entra audit — the detective control on the write boundary.
#
# ARCHITECTURE.md §2 used to prescribe Azure Policy for this, denying
# `app_role_assignment_required = false` on these applications. That is not buildable.
# Azure Policy evaluates resources represented in Azure Resource Manager; Entra app
# registrations and service principals are Microsoft Graph objects with no ARM
# representation, no resource group, and no policy alias. There is no rule to write.
#
# So the boundary gets a detective control instead of a preventive one, and it is worth
# being clear-eyed about the difference: this does not stop anyone flipping the attribute.
# It means nobody flips it quietly. Combined with tests/test_write_boundary.py — which
# blocks the change arriving through Terraform — the two cover the paths that exist:
#
#   through the repo  → the test fails in review        (preventive)
#   through the portal, CLI, or Graph → this alert fires (detective)
#
# ---------------------------------------------------------------------------
# Why this is its own module and its own root
#
# `azurerm_monitor_aad_diagnostic_setting` is TENANT-scoped. It is not in a subscription
# or a resource group, and there is one Entra tenant behind both dev and prod. Creating
# it from both environment roots would mean two roots fighting over one object, each
# reverting the other on alternate applies.
#
# It also needs permissions the environment roots deliberately do not have: Contributor
# at `/providers/Microsoft.aadiam`, granted by someone who is User Access Administrator
# at root scope. Requiring that to deploy dev would be a bad trade.
#
# Hence envs/tenant: applied once, by a different person, on a different cadence.
# ---------------------------------------------------------------------------

resource "azurerm_monitor_aad_diagnostic_setting" "audit" {
  name = "${var.name_prefix}-entra-audit"

  log_analytics_workspace_id = var.log_analytics_workspace_id

  # AuditLogs carries directory-object changes: who changed which property on which
  # service principal, and what the value became. That is the whole signal here.
  enabled_log {
    category = "AuditLogs"
  }

  # Optional and off by default. Sign-in volume for service principals is large and this
  # module does not alert on it — it is here because when the alert below does fire, the
  # next question is always "what did that principal then do", and the answer is in this
  # table or nowhere.
  dynamic "enabled_log" {
    for_each = var.capture_service_principal_signins ? [1] : []
    content {
      category = "ServicePrincipalSignInLogs"
    }
  }
}

# ---------------------------------------------------------------------------
# The alert
#
# Entra writes an `Update service principal` record when appRoleAssignmentRequired
# changes. The changed value lives in TargetResources[].modifiedProperties[], as JSON
# strings rather than native types — newValue arrives looking like "\"False\"", quotes
# and all, which is why the comparison below is `has "false"` rather than `== false`.
# `has` is case-insensitive in KQL, which is what we want: the casing is not contractual.
# ---------------------------------------------------------------------------

resource "azurerm_monitor_scheduled_query_rules_alert_v2" "role_assignment_disabled" {
  name                = "${var.name_prefix}-write-boundary-disabled"
  resource_group_name = var.resource_group_name
  location            = var.location

  scopes = [var.log_analytics_workspace_id]

  # Severity 0. Every other alert in this stack describes a workflow behaving badly; this
  # one describes the gate itself being open. There is no such thing as a routine
  # occurrence of it.
  severity             = 0
  evaluation_frequency = "PT5M"
  window_duration      = "PT10M"

  description = join(" ", [
    "app_role_assignment_required was set to false on a service principal in this stack.",
    "The write boundary is open: Entra will now issue tokens for that API to any principal",
    "in the tenant. This did not come through Terraform — the repo test blocks that path —",
    "so it was done in the portal, the CLI, or directly against Graph.",
    "Treat as an active incident. ARCHITECTURE.md §2.",
  ])

  criteria {
    # Window is wider than the frequency so a record landing late is still seen. Audit
    # log ingestion is not instant and a missed security event is worse than a duplicate.
    query = <<-KQL
      AuditLogs
      | where OperationName has "service principal" or OperationName has "application"
      | mv-expand target = TargetResources
      | where tostring(target.displayName) has "${var.name_prefix}"
      | mv-expand changed = target.modifiedProperties
      | where tostring(changed.displayName) has "AppRoleAssignmentRequired"
      | where tostring(changed.newValue) has "false"
      | project
          TimeGenerated,
          OperationName,
          principal = tostring(target.displayName),
          oldValue  = tostring(changed.oldValue),
          newValue  = tostring(changed.newValue),
          actor     = tostring(InitiatedBy.user.userPrincipalName),
          actorApp  = tostring(InitiatedBy.app.displayName)
    KQL

    operator                = "GreaterThan"
    threshold               = 0
    time_aggregation_method = "Count"

    failing_periods {
      minimum_failing_periods_to_trigger_alert = 1
      number_of_evaluation_periods             = 1
    }
  }

  # Deliberately NOT auto-mitigated, unlike the workflow alerts in modules/observability.
  # Those describe transient conditions that genuinely resolve. This one describes a
  # setting that stays wrong until a human changes it back, and an alert that clears
  # itself would suggest the problem went away on its own. It has not.
  auto_mitigation_enabled = false

  action {
    action_groups = [var.action_group_id]
  }

  tags = var.tags
}
