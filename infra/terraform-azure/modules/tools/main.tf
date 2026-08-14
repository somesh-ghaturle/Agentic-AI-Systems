# Tools — one Function App per tool, split read from write by who may call it
#
# This is where the architecture's central claim is enforced, and it is worth being
# precise about how, because Azure has no direct equivalent of a Lambda resource policy.
#
# On AWS a write tool carries an `aws_lambda_permission` naming the approval executor and
# nothing else, so the state machine simply has no route to it. The Azure analogue is
# built from two Entra facts working together:
#
#   1. `app_role_assignment_required = true` on the tool's service principal. Entra then
#      refuses to *issue a token* for this resource to any principal without an app role
#      assignment. This is the load-bearing line. Without it every workload in the tenant
#      can obtain a valid token and Easy Auth will happily accept it.
#
#   2. Easy Auth on the Function App (`auth_settings_v2`, `Return401`) rejects any request
#      arriving without a valid token for this specific audience — before a single line of
#      handler code runs.
#
# The assignment in (1) is granted to the orchestrator for read tools and to the approval
# executor for write tools. Never both. So the orchestrator cannot obtain a token for a
# write tool, and even if it somehow held one, it was minted for a different audience.
#
# ---------------------------------------------------------------------------
# The failure mode this is designed against
# ---------------------------------------------------------------------------
#
# The tempting shortcut is a function key in an app setting — a shared secret the caller
# presents. It fails the moment anything can read app settings, it appears in logs and
# diagnostic dumps, it cannot be attributed to a caller after the fact, and rotating it
# means coordinating every caller at once. Identity-based auth has none of those
# properties, which is why the credential-free path is the only one wired here.

data "azuread_client_config" "current" {}

locals {
  read_tools  = { for k, v in var.tools : k => v if v.access == "read" }
  write_tools = { for k, v in var.tools : k => v if v.access == "write" }
}

# ---------------------------------------------------------------------------
# One app registration per tool — the audience a caller must hold a token for
# ---------------------------------------------------------------------------

resource "random_uuid" "invoke_role" {
  for_each = var.tools
}

resource "azuread_application" "tool" {
  for_each = var.tools

  display_name     = "${var.name_prefix}-tool-${each.key}"
  owners           = [data.azuread_client_config.current.object_id]
  sign_in_audience = "AzureADMyOrg"

  app_role {
    allowed_member_types = ["Application"]
    description          = "Permits invoking the ${each.key} tool. Granted to exactly one caller."
    display_name         = "Tool.Invoke"
    id                   = random_uuid.invoke_role[each.key].result
    value                = "Tool.Invoke"
  }

  identifier_uris = ["api://${var.name_prefix}-tool-${each.key}"]
}

resource "azuread_service_principal" "tool" {
  for_each = var.tools

  client_id = azuread_application.tool[each.key].client_id
  owners    = [data.azuread_client_config.current.object_id]

  # THE load-bearing line. With this false, Entra issues a token for this resource to any
  # principal that asks, and the whole read/write split becomes decorative.
  app_role_assignment_required = true
}

# ---------------------------------------------------------------------------
# Who may call what — the split, stated once
# ---------------------------------------------------------------------------

resource "azuread_app_role_assignment" "read_tool_from_orchestrator" {
  for_each = local.read_tools

  app_role_id         = random_uuid.invoke_role[each.key].result
  principal_object_id = var.orchestrator_principal_id
  resource_object_id  = azuread_service_principal.tool[each.key].object_id
}

resource "azuread_app_role_assignment" "write_tool_from_executor" {
  for_each = local.write_tools

  app_role_id         = random_uuid.invoke_role[each.key].result
  principal_object_id = var.approval_executor_principal_id
  resource_object_id  = azuread_service_principal.tool[each.key].object_id

  lifecycle {
    precondition {
      condition     = var.approval_executor_principal_id != null && var.approval_executor_principal_id != ""
      error_message = "A write tool is declared but approval_executor_principal_id is unset. Applying would create a write tool nobody can invoke, or worse, tempt someone to open it up. Wire the approval module first."
    }
  }
}

# ---------------------------------------------------------------------------
# Compute
# ---------------------------------------------------------------------------

resource "azurerm_storage_account" "tools" {
  name                = replace("${var.name_prefix}toolssa", "-", "")
  resource_group_name = var.resource_group_name
  location            = var.location

  account_tier             = "Standard"
  account_replication_type = var.storage_replication_type

  # Defaults in azurerm are already TLS1_2 and HTTPS-only; stated explicitly because a
  # provider default is not a guarantee and this is a security boundary.
  min_tls_version                 = "TLS1_2"
  https_traffic_only_enabled      = true
  allow_nested_items_to_be_public = false
  shared_access_key_enabled       = var.storage_shared_access_key_enabled

  public_network_access_enabled = var.storage_public_network_access_enabled

  tags = var.tags
}

resource "azurerm_service_plan" "tools" {
  name                = "${var.name_prefix}-tools-plan"
  resource_group_name = var.resource_group_name
  location            = var.location
  os_type             = "Linux"
  sku_name            = var.service_plan_sku

  tags = var.tags
}

resource "azurerm_linux_function_app" "tool" {
  for_each = var.tools

  name                = "${var.name_prefix}-tool-${each.key}"
  resource_group_name = var.resource_group_name
  location            = var.location
  service_plan_id     = azurerm_service_plan.tools.id

  storage_account_name = azurerm_storage_account.tools.name

  # No access key. The function app authenticates to its own storage as itself, which is
  # the same reasoning as the managed identity everywhere else: a key that exists is a key
  # that can leak.
  storage_uses_managed_identity = true

  https_only = true

  identity {
    type         = "UserAssigned"
    identity_ids = [var.tool_identities[each.key].id]
  }

  # Which identity to present when talking to storage and Key Vault. With more than one
  # identity attached this is not optional — Azure will not guess.
  key_vault_reference_identity_id = var.tool_identities[each.key].id

  site_config {
    application_stack {
      python_version = var.python_version
    }

    # The analogue of Lambda reserved concurrency: bounds the blast radius of a retry
    # storm rather than letting one misbehaving tool consume the whole plan.
    app_scale_limit = each.value.max_instances

    ftps_state          = "Disabled"
    minimum_tls_version = "1.2"
  }

  app_settings = merge(
    var.common_environment,
    each.value.environment,
    {
      "FUNCTIONS_WORKER_RUNTIME" = "python"

      # src/build.sh ships SOURCE, not vendored wheels — see the header in that script for
      # why. Oryx is what turns it into a runnable app: it reads requirements.txt on the
      # build server and installs against the real Linux runtime.
      #
      # Without this the zip deploys successfully and every invocation fails at import on
      # the first `azure.identity` line, which reads as a code bug rather than a missing
      # build step.
      "SCM_DO_BUILD_DURING_DEPLOYMENT"   = "true"
      "ENABLE_ORYX_BUILD"                = "true"
      "AzureWebJobsStorage__accountName" = azurerm_storage_account.tools.name

      # storage_uses_managed_identity alone points the runtime at the SYSTEM-assigned
      # identity, which these apps do not have — only a user-assigned one is attached.
      # Without naming the credential type and the client ID, every app fails at startup
      # with a storage connection error that says nothing about identity.
      "AzureWebJobsStorage__credential" = "managedidentity"
      "AzureWebJobsStorage__clientId"   = var.tool_identities[each.key].client_id

      "TOOL_NAME"       = each.key
      "TOOL_ACCESS"     = each.value.access
      "AZURE_CLIENT_ID" = var.tool_identities[each.key].client_id
    },
  )

  # Rejects unauthenticated callers before the handler runs. Paired with
  # app_role_assignment_required above, this is the Azure form of a Lambda resource policy.
  auth_settings_v2 {
    auth_enabled           = true
    require_authentication = true
    unauthenticated_action = "Return401"
    default_provider       = "azureactivedirectory"

    active_directory_v2 {
      client_id            = azuread_application.tool[each.key].client_id
      tenant_auth_endpoint = "https://login.microsoftonline.com/${var.tenant_id}/v2.0"
      allowed_audiences = [
        "api://${var.name_prefix}-tool-${each.key}",
        azuread_application.tool[each.key].client_id,
      ]
    }

    login {}
  }

  zip_deploy_file = each.value.package_path

  tags = var.tags

  lifecycle {
    precondition {
      condition     = contains(["read", "write"], each.value.access)
      error_message = "Tool ${each.key} has access '${each.value.access}'. Only 'read' and 'write' are meaningful — anything else silently skips the split."
    }
  }
}

# The function app's own identity needs data-plane access to the storage account it runs
# from. This is what `storage_uses_managed_identity` requires in exchange for not holding
# a key.
resource "azurerm_role_assignment" "tool_storage" {
  for_each = var.tools

  scope                = azurerm_storage_account.tools.id
  role_definition_name = "Storage Blob Data Owner"
  principal_id         = var.tool_identities[each.key].principal_id
}
