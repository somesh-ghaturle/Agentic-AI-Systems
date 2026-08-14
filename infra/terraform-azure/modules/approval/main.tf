# Approval — the gate, and the only principal that may invoke a write tool
#
# What this module previously created: a Service Bus namespace, a topic, and a
# subscription. Nothing published to them, nothing consumed them, and nothing prevented a
# write tool from being invoked. The HOW-TO said it "handles gates". It did not.
#
# The gate is four things working together, and removing any one of them opens it:
#
#   1. The validator checks ownership, permission, and limits deterministically, in code,
#      and rejects invalid proposals BEFORE a human is asked. This is what keeps approval
#      requests meaningful — a reviewer shown mostly junk stops reading, and gate fatigue
#      is how a gate fails while still appearing to work.
#   2. The approval record is written before anyone is notified, carrying a fingerprint of
#      the exact arguments a human will be shown.
#   3. The orchestrator's run is SUSPENDED on a callback URL. Not polling, not sleeping —
#      genuinely parked until someone resolves it.
#   4. The executor claims the record with an ETag-conditional write, re-checks the
#      fingerprint, invokes the write tool with an idempotency key, and only then resolves
#      the callback.
#
# The executor is also the sole holder of the invoke app role on write tools — granted
# over in modules/tools, which takes this module's executor principal ID as input.

data "azurerm_subscription" "current" {}

data "azuread_client_config" "current" {}

# ---------------------------------------------------------------------------
# Who may call the gate itself
#
# An earlier version of this module left both function apps unauthenticated. That is a
# hole in the gate rather than a missing nicety: the executor is the sole principal
# permitted to invoke a write tool, so an open endpoint on it is an open endpoint on
# every write tool behind it. The claim and fingerprint checks would still reject a
# forged request, but "the second line of defence holds" is not a reason to leave the
# first one off.
#
# The two are gated differently, and the difference is the point:
#
#   validator → applications only. The orchestrator calls it; no human ever should.
#   executor  → users AND applications. It is resolved by a human clicking approve, so
#               it must admit people — but only people who have been assigned the role.
# ---------------------------------------------------------------------------

resource "random_uuid" "validator_role" {}
resource "random_uuid" "executor_role" {}

resource "azuread_application" "validator" {
  display_name     = "${var.name_prefix}-approval-validator"
  owners           = [data.azuread_client_config.current.object_id]
  sign_in_audience = "AzureADMyOrg"

  app_role {
    allowed_member_types = ["Application"]
    description          = "Permits requesting validation and opening an approval. Granted to the orchestrator only."
    display_name         = "Approval.Request"
    id                   = random_uuid.validator_role.result
    value                = "Approval.Request"
  }

  identifier_uris = ["api://${var.name_prefix}-approval-validator"]
}

resource "azuread_service_principal" "validator" {
  client_id = azuread_application.validator.client_id
  owners    = [data.azuread_client_config.current.object_id]

  app_role_assignment_required = true
}

resource "azuread_app_role_assignment" "validator_from_orchestrator" {
  app_role_id         = random_uuid.validator_role.result
  principal_object_id = var.orchestrator_principal_id
  resource_object_id  = azuread_service_principal.validator.object_id
}

resource "azuread_application" "executor" {
  display_name     = "${var.name_prefix}-approval-executor"
  owners           = [data.azuread_client_config.current.object_id]
  sign_in_audience = "AzureADMyOrg"

  app_role {
    # Users, because a human resolves an approval. This is the one place in the system
    # where a person is the caller rather than a workload.
    allowed_member_types = ["User", "Application"]
    description          = "Permits resolving an approval decision. Granted to designated approvers."
    display_name         = "Approval.Resolve"
    id                   = random_uuid.executor_role.result
    value                = "Approval.Resolve"
  }

  identifier_uris = ["api://${var.name_prefix}-approval-executor"]
}

resource "azuread_service_principal" "executor" {
  client_id = azuread_application.executor.client_id
  owners    = [data.azuread_client_config.current.object_id]

  # Without this, any authenticated user in the tenant can approve anything. That is not
  # an approval gate — it is a login page in front of one.
  app_role_assignment_required = true
}

resource "azuread_app_role_assignment" "executor_from_approver" {
  for_each = var.approver_principal_ids

  app_role_id         = random_uuid.executor_role.result
  principal_object_id = each.value
  resource_object_id  = azuread_service_principal.executor.object_id
}

# ---------------------------------------------------------------------------
# Approval records
#
# Cosmos rather than Table Storage, for one reason that matters: the claim in step 4 is a
# conditional write. Cosmos gives ETag/If-Match optimistic concurrency, which is the
# direct analogue of DynamoDB's ConditionExpression. Without it, a double-clicked approve
# button executes twice.
# ---------------------------------------------------------------------------

resource "azurerm_cosmosdb_account" "approvals" {
  name                = "${var.name_prefix}-approvals"
  resource_group_name = var.resource_group_name
  location            = var.location
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"

  # Serverless: this is an audit trail with human-paced write volume, not a hot path.
  # Provisioned throughput here would bill continuously for capacity nobody uses.
  capabilities {
    name = "EnableServerless"
  }

  consistency_policy {
    # Strong, deliberately. The claim in step 4 reads its own write back; under eventual
    # consistency a second executor can read a stale "pending" and claim an already-
    # claimed record, which is the exact double-execution this gate exists to prevent.
    consistency_level = "Strong"
  }

  geo_location {
    location          = var.location
    failover_priority = 0
  }

  # PITR on the approval trail. This is the record of who authorized what, so losing it
  # to a bad deploy is a compliance problem rather than an inconvenience.
  dynamic "backup" {
    for_each = var.enable_continuous_backup ? [1] : []
    content {
      type = "Continuous"
      tier = "Continuous7Days"
    }
  }

  public_network_access_enabled     = var.cosmos_public_network_access_enabled
  is_virtual_network_filter_enabled = var.cosmos_public_network_access_enabled == false

  # Key-based auth to Cosmos should be off — every caller here uses its managed identity
  # via the SQL role assignments below, so the account keys grant a path nothing
  # legitimate needs. The provider attribute that did this is deprecated and its
  # replacement is not pinned in this repo's provider version, so it is deliberately not
  # set here rather than guessed at. Enforce it with Azure Policy
  # ("Cosmos DB database accounts should have local authentication methods disabled")
  # until this is re-pinned. Tracked in ARCHITECTURE.md section "Remaining work".

  tags = var.tags
}

resource "azurerm_cosmosdb_sql_database" "agentic" {
  name                = "agentic"
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.approvals.name
}

resource "azurerm_cosmosdb_sql_container" "approvals" {
  name                  = "approvals"
  resource_group_name   = var.resource_group_name
  account_name          = azurerm_cosmosdb_account.approvals.name
  database_name         = azurerm_cosmosdb_sql_database.agentic.name
  partition_key_paths   = ["/approval_id"]
  partition_key_version = 2

  # Never expire approval records by default. This is the audit trail; a TTL on it is a
  # decision about record retention, not a storage optimization, so it is set explicitly
  # from the environment or not at all.
  default_ttl = var.approval_record_ttl_seconds
}

# ---------------------------------------------------------------------------
# Notification
# ---------------------------------------------------------------------------

resource "azurerm_servicebus_namespace" "approval" {
  name                = "${var.name_prefix}-approval-sb"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = var.servicebus_sku
  capacity            = var.servicebus_sku == "Premium" ? var.servicebus_capacity : 0

  # Managed identity everywhere else means nothing needs a SAS connection string here.
  local_auth_enabled = var.servicebus_local_auth_enabled

  minimum_tls_version = "1.2"

  public_network_access_enabled = var.servicebus_public_network_access_enabled

  tags = var.tags
}

resource "azurerm_servicebus_topic" "approval" {
  name         = "approval-requests"
  namespace_id = azurerm_servicebus_namespace.approval.id
}

resource "azurerm_servicebus_subscription" "approval" {
  name               = "approval-sub"
  topic_id           = azurerm_servicebus_topic.approval.id
  max_delivery_count = 10

  # Undeliverable approval requests must not vanish. A silently dropped message is an
  # execution that hangs until its window closes with nobody knowing why.
  dead_lettering_on_message_expiration = true
}

# ---------------------------------------------------------------------------
# Validator and executor
# ---------------------------------------------------------------------------

resource "azurerm_storage_account" "approval" {
  name                = replace("${var.name_prefix}approvalsa", "-", "")
  resource_group_name = var.resource_group_name
  location            = var.location

  account_tier             = "Standard"
  account_replication_type = var.storage_replication_type

  min_tls_version                 = "TLS1_2"
  https_traffic_only_enabled      = true
  allow_nested_items_to_be_public = false
  shared_access_key_enabled       = var.storage_shared_access_key_enabled
  public_network_access_enabled   = var.storage_public_network_access_enabled

  tags = var.tags
}

resource "azurerm_service_plan" "approval" {
  name                = "${var.name_prefix}-approval-plan"
  resource_group_name = var.resource_group_name
  location            = var.location
  os_type             = "Linux"
  sku_name            = var.service_plan_sku

  tags = var.tags
}

locals {
  functions = {
    validator = {
      identity     = var.validator_identity
      package_path = var.validator_package_path
      settings     = var.validator_environment
      application  = azuread_application.validator
      audience     = "api://${var.name_prefix}-approval-validator"
    }
    executor = {
      identity     = var.executor_identity
      package_path = var.executor_package_path
      settings     = var.executor_environment
      application  = azuread_application.executor
      audience     = "api://${var.name_prefix}-approval-executor"
    }
  }

  cosmos_data_contributor_role_id = "${azurerm_cosmosdb_account.approvals.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002"
}

resource "azurerm_linux_function_app" "approval" {
  for_each = local.functions

  name                = "${var.name_prefix}-approval-${each.key}"
  resource_group_name = var.resource_group_name
  location            = var.location
  service_plan_id     = azurerm_service_plan.approval.id

  storage_account_name          = azurerm_storage_account.approval.name
  storage_uses_managed_identity = true

  https_only = true

  identity {
    type         = "UserAssigned"
    identity_ids = [each.value.identity.id]
  }

  key_vault_reference_identity_id = each.value.identity.id

  site_config {
    application_stack {
      python_version = var.python_version
    }

    ftps_state          = "Disabled"
    minimum_tls_version = "1.2"
  }

  app_settings = merge(
    var.common_environment,
    each.value.settings,
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
      "AzureWebJobsStorage__accountName" = azurerm_storage_account.approval.name

      # See the same settings in modules/tools: storage_uses_managed_identity points the
      # runtime at a system-assigned identity these apps do not have. Naming the
      # credential type and client ID is what makes the user-assigned identity apply.
      "AzureWebJobsStorage__credential" = "managedidentity"
      "AzureWebJobsStorage__clientId"   = each.value.identity.client_id

      "AZURE_CLIENT_ID"      = each.value.identity.client_id
      "COSMOS_ENDPOINT"      = azurerm_cosmosdb_account.approvals.endpoint
      "COSMOS_DATABASE"      = azurerm_cosmosdb_sql_database.agentic.name
      "APPROVALS_CONTAINER"  = azurerm_cosmosdb_sql_container.approvals.name
      "SERVICEBUS_NAMESPACE" = azurerm_servicebus_namespace.approval.name
      "APPROVAL_TOPIC"       = azurerm_servicebus_topic.approval.name
    },
  )

  # Rejects unauthenticated callers before the handler runs. Paired with
  # app_role_assignment_required above, this is what stops anyone who can reach the URL
  # from opening or resolving an approval.
  auth_settings_v2 {
    auth_enabled           = true
    require_authentication = true
    unauthenticated_action = "Return401"
    default_provider       = "azureactivedirectory"

    active_directory_v2 {
      client_id            = each.value.application.client_id
      tenant_auth_endpoint = "https://login.microsoftonline.com/${var.tenant_id}/v2.0"
      allowed_audiences = [
        each.value.audience,
        each.value.application.client_id,
      ]
    }

    login {}
  }

  zip_deploy_file = each.value.package_path

  tags = var.tags
}

# ---------------------------------------------------------------------------
# What each of them may touch
# ---------------------------------------------------------------------------

resource "azurerm_role_assignment" "approval_storage" {
  for_each = local.functions

  scope                = azurerm_storage_account.approval.id
  role_definition_name = "Storage Blob Data Owner"
  principal_id         = each.value.identity.principal_id
}

# Both read and write approval records: the validator creates them, the executor claims
# and resolves them.
resource "azurerm_cosmosdb_sql_role_assignment" "approval_data" {
  for_each = local.functions

  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.approvals.name
  role_definition_id  = local.cosmos_data_contributor_role_id
  principal_id        = each.value.identity.principal_id
  scope               = azurerm_cosmosdb_account.approvals.id
}

# Only the validator publishes approval requests. The executor has no send rights — it
# consumes decisions, it does not manufacture them.
resource "azurerm_role_assignment" "validator_topic_send" {
  scope                = azurerm_servicebus_topic.approval.id
  role_definition_name = "Azure Service Bus Data Sender"
  principal_id         = var.validator_identity.principal_id
}
