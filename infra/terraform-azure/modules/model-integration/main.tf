# Model integration — the account, the deployment, and the content filter.
#
# This module was a comment-only placeholder that returned whatever endpoint you passed
# into it. That was defensible on one point and wrong on the rest: an Azure OpenAI account
# genuinely can require subscription-level access approval, so a module that creates one
# unconditionally is a module that fails to apply in a tenant without it.
#
# The fix is a switch, not an omission. `create_account = false` keeps the old behaviour —
# bring your own endpoint — and is the default. `create_account = true` provisions the
# account, the deployment, and the content filter that is Azure's answer to the Bedrock
# guardrail in terraform-aws/modules/security.
#
# ---------------------------------------------------------------------------
# The guardrail equivalence, and where it stops
# ---------------------------------------------------------------------------
#
# terraform-aws creates an `aws_bedrock_guardrail` and is explicit about its status:
#
#   "a mitigation layer, not the control. Worth having: it catches a meaningful share of
#    injection attempts and PII leakage cheaply. Worth being honest about: a determined
#    injection will get past it, which is exactly why the write path is gated separately."
#
# Everything in that paragraph applies here unchanged. The Azure mechanism is a Responsible
# AI policy attached to the deployment, and it covers the same ground for content
# categories — hate, sexual, violence, self-harm — plus prompt-injection detection
# ("jailbreak") that Bedrock exposes separately.
#
# Where it stops, and this is the real asymmetry: **there is no PII filter here.**
# `aws_bedrock_guardrail` takes a `sensitive_information_policy_config` that masks or
# blocks PII entities at the model boundary. Azure's RAI policies have no equivalent — PII
# detection lives in a different service (Language / Presidio) and is not attachable to a
# deployment. So the AWS tree's backstop for what upstream masking misses does not exist on
# Azure, and PRODUCTION-PRINCIPLES.md's requirement that masking happen before data reaches
# the model is, on this tree, entirely a property of handler code.
#
# That is a gap in the mitigation layer, not in the control. The write boundary is
# unaffected.
# ---------------------------------------------------------------------------

locals {
  create = var.create_account

  # The endpoint consumers actually use: the created account's, or the one supplied.
  # Written once here so no consumer has to know which mode the module is in.
  endpoint = local.create ? azurerm_cognitive_account.openai[0].endpoint : var.azure_openai_endpoint

  deployment_name = local.create ? azurerm_cognitive_deployment.model[0].name : var.model_deployment_name
}

resource "azurerm_cognitive_account" "openai" {
  count = local.create ? 1 : 0

  name                = "${var.name_prefix}-openai"
  resource_group_name = var.resource_group_name
  location            = var.location
  kind                = "OpenAI"
  sku_name            = var.sku_name

  # A custom subdomain is not cosmetic: token-based auth against a Cognitive Services
  # account requires one. Without it the account only accepts API keys, which is the
  # credential this tree spends its identity module avoiding.
  custom_subdomain_name = "${var.name_prefix}-openai"

  # ---------------------------------------------------------------------------
  # No API keys
  #
  # With this false the account refuses key auth outright and `Cognitive Services OpenAI
  # User` below is the only route in. The reasoning tool already has a managed identity;
  # a key would be a second, worse way in — one that appears in the portal, survives
  # identity revocation, and cannot be attributed to a caller after the fact.
  # ---------------------------------------------------------------------------
  local_auth_enabled = var.local_auth_enabled

  public_network_access_enabled = var.public_network_access_enabled

  identity {
    type = "SystemAssigned"
  }

  tags = merge(var.tags, {
    Component = "openai"
    Layer     = "model"
  })

  lifecycle {
    precondition {
      condition     = !var.local_auth_enabled || var.allow_local_auth_acknowledged
      error_message = "local_auth_enabled is true, which leaves API keys valid on the model account. Every other credential in this tree is a managed identity precisely so there is nothing to leak or rotate. If you need keys anyway, set allow_local_auth_acknowledged = true to say so deliberately."
    }
  }
}

# ---------------------------------------------------------------------------
# The content filter — Azure's guardrail
#
# Attached to the deployment below. Unattached, it exists and does nothing, which is the
# failure mode worth watching for: the policy shows up in the portal, looks like a control,
# and filters nothing.
# ---------------------------------------------------------------------------

resource "azurerm_cognitive_account_rai_policy" "guardrail" {
  count = local.create && var.create_content_filter ? 1 : 0

  name                 = "${var.name_prefix}-guardrail"
  cognitive_account_id = azurerm_cognitive_account.openai[0].id

  # Microsoft's default policy is the floor this builds on. Naming it explicitly means an
  # Azure-side default change is visible as a diff rather than absorbed silently.
  base_policy_name = var.base_policy_name

  dynamic "content_filter" {
    for_each = var.content_filters
    content {
      name               = content_filter.value.name
      filter_enabled     = content_filter.value.enabled
      block_enabled      = content_filter.value.block
      severity_threshold = content_filter.value.severity_threshold
      source             = content_filter.value.source
    }
  }

  tags = var.tags
}

resource "azurerm_cognitive_deployment" "model" {
  count = local.create ? 1 : 0

  name                 = var.model_deployment_name
  cognitive_account_id = azurerm_cognitive_account.openai[0].id

  # Naming the filter here is what makes it apply. See the note above the policy.
  rai_policy_name = var.create_content_filter ? azurerm_cognitive_account_rai_policy.guardrail[0].name : null

  model {
    format  = "OpenAI"
    name    = var.model_name
    version = var.model_version
  }

  sku {
    name = var.deployment_sku_name

    # Tokens per minute, in thousands. This is the closest thing to a spend ceiling the
    # model layer has: an agent in a retry loop is bounded by throughput before it is
    # bounded by the daily cost alarm, which only fires after the money is spent.
    capacity = var.deployment_capacity
  }

  # Azure retires model versions on a published schedule and auto-upgrade moves the
  # deployment when that happens. Off by default: a model that changes underneath a
  # prompt-versioned reasoning step makes results non-reproducible, and the trace record
  # would attribute the change to nothing.
  version_upgrade_option = var.version_upgrade_option
}

# ---------------------------------------------------------------------------
# Who may call the model
#
# The reasoning tool's identity, and nothing else. `Cognitive Services OpenAI User` permits
# inference and not deployment management — a compromised reasoning tool can spend money
# and cannot change which model runs or remove the content filter in front of it.
# ---------------------------------------------------------------------------

resource "azurerm_role_assignment" "model_user" {
  for_each = local.create ? var.caller_principal_ids : {}

  scope                = azurerm_cognitive_account.openai[0].id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = each.value
}

resource "azurerm_monitor_diagnostic_setting" "openai" {
  count = local.create && var.log_analytics_workspace_id != null ? 1 : 0

  name                       = "${var.name_prefix}-openai-diag"
  target_resource_id         = azurerm_cognitive_account.openai[0].id
  log_analytics_workspace_id = var.log_analytics_workspace_id

  # Every request and response the model handled, including what the content filter caught.
  # This is the evidence trail behind a refusal, and without it a blocked request is
  # indistinguishable from a broken one.
  enabled_log {
    category = "RequestResponse"
  }

  enabled_log {
    category = "Audit"
  }

  enabled_metric {
    category = "AllMetrics"
  }
}
