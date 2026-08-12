# Observability — the destination, the routing, and the alerts
#
# Terraform can create the workspace, the retention, the queries, and the alert rules. It
# cannot make your application emit the fields those queries read. The trace schema is
# documented in outputs.tf; emitting it is application work.
#
# ---------------------------------------------------------------------------
# The single most important structural decision here
# ---------------------------------------------------------------------------
#
# Every alert below queries ONE table: FunctionAppLogs, filtered to this environment's
# apps. Not each app's own logs, not Application Insights per component. A handler that
# writes only to its own component's logs looks perfectly healthy in the portal and is
# invisible to every alert in this file.
#
# Azure makes this easy to get wrong in a way AWS does not. Function App logs do not
# reach a Log Analytics workspace by default — they need an explicit diagnostic setting,
# created below for each app. Miss one app and it drops out of every query silently;
# nothing errors, the alert just never fires for that component.
#
# ---------------------------------------------------------------------------
# Why there is a trace emitter, and why it is not a tool
# ---------------------------------------------------------------------------
#
# The Logic App's own records — the terminal outcome of a request, the loop bound firing
# — are produced inside the workflow, and workflow run history lands in a different table
# with a different shape. Two of the alerts below would match nothing.
#
# So the workflow calls a small function that writes a trace record like any handler,
# putting the orchestrator's records in the same table as everyone else's. This is the
# direct analogue of the AWS trace_emitter and it exists for the same reason.
#
# It lives here rather than in modules/tools deliberately. It is not a tool: the model
# never proposes it, it takes no arguments from the model, and classifying it as a read
# tool would put a thing that writes audit records on the liberally-available side of the
# read/write split.

resource "azurerm_log_analytics_workspace" "law" {
  name                = "${var.name_prefix}-law"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "PerGB2018"
  retention_in_days   = var.log_retention_days

  tags = var.tags
}

# ---------------------------------------------------------------------------
# Routing — without these the workspace stays empty and every alert reads as healthy
# ---------------------------------------------------------------------------

resource "azurerm_monitor_diagnostic_setting" "function_apps" {
  for_each = var.function_app_ids

  name                       = "${var.name_prefix}-diag"
  target_resource_id         = each.value
  log_analytics_workspace_id = azurerm_log_analytics_workspace.law.id

  enabled_log {
    category = "FunctionAppLogs"
  }

  enabled_metric {
    category = "AllMetrics"
  }
}

resource "azurerm_monitor_diagnostic_setting" "logic_app" {
  count = var.logic_app_id == null ? 0 : 1

  name                       = "${var.name_prefix}-diag"
  target_resource_id         = var.logic_app_id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.law.id

  enabled_log {
    category = "WorkflowRuntime"
  }

  enabled_metric {
    category = "AllMetrics"
  }
}

# ---------------------------------------------------------------------------
# Trace emitter
#
# Its own app registration, gated the same way the tools are: the orchestrator holds an
# app role and nothing else can obtain a token. This function writes audit records, so an
# open endpoint here means anyone can forge them — which is worse than an open read tool,
# not better.
# ---------------------------------------------------------------------------

data "azuread_client_config" "current" {}

resource "random_uuid" "trace_emitter_role" {
  count = var.trace_emitter == null ? 0 : 1
}

resource "azuread_application" "trace_emitter" {
  count = var.trace_emitter == null ? 0 : 1

  display_name     = "${var.name_prefix}-trace-emitter"
  owners           = [data.azuread_client_config.current.object_id]
  sign_in_audience = "AzureADMyOrg"

  app_role {
    allowed_member_types = ["Application"]
    description          = "Permits writing a trace record. Granted to the orchestrator only."
    display_name         = "Trace.Emit"
    id                   = random_uuid.trace_emitter_role[0].result
    value                = "Trace.Emit"
  }

  identifier_uris = ["api://${var.name_prefix}-trace-emitter"]
}

resource "azuread_service_principal" "trace_emitter" {
  count = var.trace_emitter == null ? 0 : 1

  client_id = azuread_application.trace_emitter[0].client_id
  owners    = [data.azuread_client_config.current.object_id]

  # Same load-bearing line as modules/tools. False here means any principal in the tenant
  # can write to the audit trail.
  app_role_assignment_required = true
}

resource "azuread_app_role_assignment" "trace_emitter_from_orchestrator" {
  count = var.trace_emitter == null ? 0 : 1

  app_role_id         = random_uuid.trace_emitter_role[0].result
  principal_object_id = var.trace_emitter.orchestrator_principal_id
  resource_object_id  = azuread_service_principal.trace_emitter[0].object_id
}

resource "azurerm_storage_account" "observability" {
  count = var.trace_emitter == null ? 0 : 1

  name                = replace("${var.name_prefix}obssa", "-", "")
  resource_group_name = var.resource_group_name
  location            = var.location

  account_tier             = "Standard"
  account_replication_type = var.storage_replication_type

  min_tls_version                 = "TLS1_2"
  https_traffic_only_enabled      = true
  allow_nested_items_to_be_public = false

  tags = var.tags
}

resource "azurerm_service_plan" "observability" {
  count = var.trace_emitter == null ? 0 : 1

  name                = "${var.name_prefix}-obs-plan"
  resource_group_name = var.resource_group_name
  location            = var.location
  os_type             = "Linux"
  sku_name            = var.service_plan_sku

  tags = var.tags
}

resource "azurerm_linux_function_app" "trace_emitter" {
  count = var.trace_emitter == null ? 0 : 1

  name                = "${var.name_prefix}-trace-emitter"
  resource_group_name = var.resource_group_name
  location            = var.location
  service_plan_id     = azurerm_service_plan.observability[0].id

  storage_account_name          = azurerm_storage_account.observability[0].name
  storage_uses_managed_identity = true

  https_only = true

  identity {
    type         = "UserAssigned"
    identity_ids = [var.trace_emitter.identity.id]
  }

  key_vault_reference_identity_id = var.trace_emitter.identity.id

  site_config {
    application_stack {
      python_version = var.python_version
    }

    ftps_state          = "Disabled"
    minimum_tls_version = "1.2"
  }

  app_settings = {
    "FUNCTIONS_WORKER_RUNTIME"         = "python"
    "AzureWebJobsStorage__accountName" = azurerm_storage_account.observability[0].name
    "AzureWebJobsStorage__credential"  = "managedidentity"
    "AzureWebJobsStorage__clientId"    = var.trace_emitter.identity.client_id
    "AZURE_CLIENT_ID"                  = var.trace_emitter.identity.client_id
  }

  # Same Easy Auth posture as every other function here. This one writes audit records —
  # leaving it open would let anyone forge them.
  auth_settings_v2 {
    auth_enabled           = true
    require_authentication = true
    unauthenticated_action = "Return401"
    default_provider       = "azureactivedirectory"

    active_directory_v2 {
      client_id            = azuread_application.trace_emitter[0].client_id
      tenant_auth_endpoint = "https://login.microsoftonline.com/${var.tenant_id}/v2.0"
      allowed_audiences = [
        "api://${var.name_prefix}-trace-emitter",
        azuread_application.trace_emitter[0].client_id,
      ]
    }

    login {}
  }

  zip_deploy_file = var.trace_emitter.package_path

  tags = var.tags
}

resource "azurerm_role_assignment" "trace_emitter_storage" {
  count = var.trace_emitter == null ? 0 : 1

  scope                = azurerm_storage_account.observability[0].id
  role_definition_name = "Storage Blob Data Owner"
  principal_id         = var.trace_emitter.identity.principal_id
}

# ---------------------------------------------------------------------------
# Who gets told
# ---------------------------------------------------------------------------

resource "azurerm_monitor_action_group" "alerts" {
  name                = "${var.name_prefix}-alerts"
  resource_group_name = var.resource_group_name
  short_name          = substr(replace(var.name_prefix, "-", ""), 0, 12)

  dynamic "email_receiver" {
    for_each = var.alert_email_receivers
    content {
      name                    = email_receiver.key
      email_address           = email_receiver.value
      use_common_alert_schema = true
    }
  }

  dynamic "webhook_receiver" {
    for_each = var.alert_webhook_receivers
    content {
      name                    = webhook_receiver.key
      service_uri             = webhook_receiver.value
      use_common_alert_schema = true
    }
  }

  tags = var.tags
}

# ---------------------------------------------------------------------------
# Alerts — on the failure modes the architecture actually names
#
# Each query narrows to this environment's apps by name prefix. A workspace shared with
# another environment would otherwise have dev traces firing prod alerts.
# ---------------------------------------------------------------------------

locals {
  # Every query starts here: one table, this environment's apps, parsed as JSON. Handlers
  # print one JSON object per line; anything that is not JSON parses to null and is
  # dropped by the event_type filter rather than erroring.
  trace_prelude = <<-KQL
    let traces = FunctionAppLogs
    | where _ResourceId has "${var.name_prefix}"
    | extend trace = parse_json(Message)
    | where isnotempty(trace.event_type);
  KQL

  # Alerts that fire on any occurrence share this shape. Threshold 0, GreaterThan, so a
  # single event is enough — these are not rate problems.
  any_occurrence = {
    operator                = "GreaterThan"
    threshold               = 0
    time_aggregation_method = "Count"
  }
}

resource "azurerm_monitor_scheduled_query_rules_alert_v2" "loop_bound" {
  name                = "${var.name_prefix}-loop-bound-exceeded"
  resource_group_name = var.resource_group_name
  location            = var.location

  scopes               = [azurerm_log_analytics_workspace.law.id]
  severity             = 2
  evaluation_frequency = "PT5M"
  window_duration      = "PT5M"

  description = "An agent loop hit its step bound. Every occurrence is a workflow that could not complete within budget — worth investigating, never worth ignoring."

  criteria {
    query = <<-KQL
      ${local.trace_prelude}
      traces
      | where tostring(trace.event_type) == "loop_bound_exceeded"
    KQL

    operator                = local.any_occurrence.operator
    threshold               = local.any_occurrence.threshold
    time_aggregation_method = local.any_occurrence.time_aggregation_method

    failing_periods {
      minimum_failing_periods_to_trigger_alert = 1
      number_of_evaluation_periods             = 1
    }
  }

  # Without this the rule resolves and re-fires on every evaluation while the condition
  # persists, which trains people to ignore it.
  auto_mitigation_enabled = true

  action {
    action_groups = [azurerm_monitor_action_group.alerts.id]
  }

  tags = var.tags
}

resource "azurerm_monitor_scheduled_query_rules_alert_v2" "schema_failures" {
  count = var.schema_failure_threshold == null ? 0 : 1

  name                = "${var.name_prefix}-schema-failures"
  resource_group_name = var.resource_group_name
  location            = var.location

  scopes               = [azurerm_log_analytics_workspace.law.id]
  severity             = 3
  evaluation_frequency = "PT5M"
  window_duration      = "PT5M"

  description = "Structured output contracts failing validation. Usually means a model or prompt version changed underneath you."

  criteria {
    query = <<-KQL
      ${local.trace_prelude}
      traces
      | where tostring(trace.event_type) == "schema_validation_failed"
    KQL

    operator                = "GreaterThan"
    threshold               = var.schema_failure_threshold
    time_aggregation_method = "Count"

    failing_periods {
      minimum_failing_periods_to_trigger_alert = 1
      number_of_evaluation_periods             = 1
    }
  }

  auto_mitigation_enabled = true

  action {
    action_groups = [azurerm_monitor_action_group.alerts.id]
  }

  tags = var.tags
}

# A workflow blocked on a human is invisible in ordinary failure metrics — it is not
# failing, it is waiting. Long waits are their own failure mode, and gate fatigue starts
# here.
#
# This watches the trace record rather than a Logic App metric: the workflow catches its
# own approval timeout and ends cleanly, so RunsFailed never sees it.
resource "azurerm_monitor_scheduled_query_rules_alert_v2" "approvals_abandoned" {
  name                = "${var.name_prefix}-approvals-abandoned"
  resource_group_name = var.resource_group_name
  location            = var.location

  scopes               = [azurerm_log_analytics_workspace.law.id]
  severity             = 2
  evaluation_frequency = "PT30M"
  window_duration      = "PT1H"

  description = "An approval window closed with nobody answering. Check that notifications are being delivered and that reviewers are still reading them — this is where gate fatigue shows up first."

  criteria {
    query = <<-KQL
      ${local.trace_prelude}
      traces
      | where tostring(trace.event_type) == "approval_abandoned"
    KQL

    operator                = local.any_occurrence.operator
    threshold               = local.any_occurrence.threshold
    time_aggregation_method = local.any_occurrence.time_aggregation_method

    failing_periods {
      minimum_failing_periods_to_trigger_alert = 1
      number_of_evaluation_periods             = 1
    }
  }

  auto_mitigation_enabled = true

  action {
    action_groups = [azurerm_monitor_action_group.alerts.id]
  }

  tags = var.tags
}

# Spend, summed over a day. cost_usd belongs on the TERMINAL record only — summing it
# across every step multiply-counts the request.
resource "azurerm_monitor_scheduled_query_rules_alert_v2" "daily_cost" {
  count = var.daily_cost_threshold_usd == null ? 0 : 1

  name                = "${var.name_prefix}-daily-cost"
  resource_group_name = var.resource_group_name
  location            = var.location

  scopes               = [azurerm_log_analytics_workspace.law.id]
  severity             = 2
  evaluation_frequency = "PT1H"
  window_duration      = "P1D"

  description = "Daily spend exceeded threshold. Usual causes: an unbounded loop, a routing regression sending cheap steps to a frontier model, or unbounded context growth."

  criteria {
    query = <<-KQL
      ${local.trace_prelude}
      traces
      | where tostring(trace.event_type) == "request_complete"
      | extend cost_usd = todouble(trace.cost_usd)
      | where isnotnull(cost_usd)
      | summarize AggregatedValue = sum(cost_usd) by bin(TimeGenerated, 1d)
    KQL

    operator                = "GreaterThan"
    threshold               = var.daily_cost_threshold_usd
    time_aggregation_method = "Total"
    metric_measure_column   = "AggregatedValue"

    failing_periods {
      minimum_failing_periods_to_trigger_alert = 1
      number_of_evaluation_periods             = 1
    }
  }

  auto_mitigation_enabled = true

  action {
    action_groups = [azurerm_monitor_action_group.alerts.id]
  }

  tags = var.tags
}

# ---------------------------------------------------------------------------
# Platform metrics — the orchestrator failing outright, which no trace record covers
# because a workflow that dies does not get to write one.
# ---------------------------------------------------------------------------

resource "azurerm_monitor_metric_alert" "orchestrator_failures" {
  count = var.logic_app_id == null ? 0 : 1

  name                = "${var.name_prefix}-orchestrator-failures"
  resource_group_name = var.resource_group_name
  scopes              = [var.logic_app_id]

  description = "Orchestrator workflow runs failing."
  severity    = 1
  frequency   = "PT5M"
  window_size = "PT15M"

  criteria {
    metric_namespace = "Microsoft.Logic/workflows"
    metric_name      = "RunsFailed"
    aggregation      = "Total"
    operator         = "GreaterThan"
    threshold        = var.execution_failure_threshold
  }

  action {
    action_group_id = azurerm_monitor_action_group.alerts.id
  }

  tags = var.tags
}
