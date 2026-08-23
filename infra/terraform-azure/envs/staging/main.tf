# Staging environment.
#
# Structurally identical to dev and prod — same modules, same wiring, same order. Every
# difference is a variable value, which is the rule the other two environments follow.
#
# What staging is FOR, since "between dev and prod" does not say much on its own: the
# dev/prod difference in this tree is not scale, it is posture. Dev runs on Consumption
# plans, with storage shared keys enabled, a public search endpoint, and no purge
# protection. Those are exactly the settings whose first real exercise would otherwise be
# the first prod apply.
#
# Two of them cannot be rehearsed any other way:
#
#   Elastic Premium   Y1 cannot join a VNet. On Consumption every private endpoint in this
#                     stack is unreachable, so a dev run proves nothing about whether prod
#                     can actually reach its own search service.
#   Shared keys off   Every caller authenticates as itself in prod. Tooling that quietly
#                     depended on an account key works in dev and fails here, which is
#                     the entire point of here.
#
# The rule for what staging takes from where:
#
#   From prod — every REVERSIBLE control
#     Function/plan tier      EP1, so the VNet path is real
#     Storage shared keys     off
#     Service Bus local auth  off
#     Search public access    closed when DNS zones are supplied
#     Trace schema alerting   threshold 0, as strict as prod
#     Step budgets            prod's, not dev's
#
#   From dev — everything IRREVERSIBLE, plus pure durability
#     Vault purge protection  off — a purge-protected vault cannot be torn down
#     Archive immutability    off — a WORM lock commits the resource group for years
#     Cosmos continuous backup off — it cannot be switched back off once enabled
#     Replication             LRS, not ZRS/GRS
#     Retention               30 days, archive expires at 90
#
# The three "off" lines in the second group are one-way doors in Azure. Turning any of
# them on here would produce an environment that cannot be destroyed and rebuilt, and a
# staging environment that is not rebuilt regularly stops resembling anything.
#
# See envs/dev/main.tf for how the two dependency cycles are broken. The reasoning is the
# same here and is not repeated.

terraform {
  # Staging is shared by definition — it is where more than one person verifies a release
  # — so local state has the same problem here it has in prod: two operators applying at
  # once corrupt each other's work and there is no lock to stop them.
  #
  # backend "azurerm" {
  #   resource_group_name  = "<tf-state-rg>"
  #   storage_account_name = "<tfstatesa>"
  #   container_name       = "tfstate"
  #   key                  = "agentic/staging.tfstate"
  #   use_azuread_auth     = true
  # }
  backend "local" {}
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

provider "azuread" {}

data "azurerm_client_config" "current" {}

locals {
  name_prefix         = "${var.project}-staging"
  resource_group_name = "${var.project}-staging-rg"

  tool_identity_names = { for name in keys(var.tools) : name => "tool-${replace(name, "_", "-")}" }

  identity_names = toset(concat(
    ["orchestrator", "approval-validator", "approval-executor", "trace-emitter"],
    values(local.tool_identity_names),
  ))

  logic_app_id = "/subscriptions/${var.subscription_id}/resourceGroups/${local.resource_group_name}/providers/Microsoft.Logic/workflows/${local.name_prefix}-orchestrator"

  # The same cycle-breaker, for the same reason, on a third edge. See envs/dev/main.tf.
  log_analytics_workspace_id = "/subscriptions/${var.subscription_id}/resourceGroups/${local.resource_group_name}/providers/Microsoft.OperationalInsights/workspaces/${local.name_prefix}-law"

  tags = {
    Project     = var.project
    Environment = "staging"
    ManagedBy   = "terraform"
    Component   = "agentic-system"
  }
}

module "networking" {
  source = "../../modules/networking"

  name_prefix         = local.name_prefix
  resource_group_name = local.resource_group_name
  location            = var.location

  tags = local.tags
}

module "identity" {
  source = "../../modules/identity"

  name_prefix         = local.name_prefix
  resource_group_name = module.networking.resource_group_name
  location            = var.location
  identities          = local.identity_names

  tags = local.tags
}

module "security" {
  source = "../../modules/security"

  name_prefix         = local.name_prefix
  resource_group_name = module.networking.resource_group_name
  location            = var.location
  tenant_id           = data.azurerm_client_config.current.tenant_id

  secret_reader_principal_ids = {
    for name, identity in module.identity.identities : name => identity.principal_id
  }

  # Dev's setting, and one of the one-way doors. Purge protection cannot be disabled once
  # enabled — not by the subscription owner, not by support — so a staging vault that had
  # it on could not be torn down and recreated the same afternoon. That teardown is what
  # keeps staging honest, so it wins here.
  purge_protection_enabled   = false
  soft_delete_retention_days = 7

  create_model_key_secret = false

  tags = local.tags
}

module "state" {
  source = "../../modules/state"

  name_prefix         = local.name_prefix
  resource_group_name = module.networking.resource_group_name
  location            = var.location

  # LRS, not prod's ZRS. Zone redundancy buys durability and changes no behaviour a
  # rehearsal can observe — a staging run cannot tell which zones its table lives in.
  account_replication_type = "LRS"

  tags = local.tags
}

module "archive" {
  source = "../../modules/archive"

  name_prefix         = local.name_prefix
  resource_group_name = module.networking.resource_group_name
  location            = var.location

  # Dev's lifecycle and dev's replication. Staging traces are the output of a release
  # rehearsal, not evidence, and the next release replaces them.
  account_replication_type = "LRS"
  transition_cool_days     = 7
  transition_archive_days  = 30
  expiration_days          = var.archive_expiration_days

  # Shared keys off, as in prod. Unlike the two lines above, this one is behavioural: it
  # is how you find out that a script, an exporter, or a support runbook was reaching the
  # archive with an account key rather than an identity.
  shared_access_key_enabled = false

  # No WORM, and deliberately not a variable — see the note in variables.tf. A locked
  # immutability policy commits this resource group for the length of the window, which
  # for prod is seven years. Staging must remain destroyable.
  immutability_period_days = null
  lock_immutability_policy = false

  tags = local.tags
}

module "knowledge" {
  source = "../../modules/knowledge"

  name_prefix         = local.name_prefix
  resource_group_name = module.networking.resource_group_name
  location            = var.location

  # Prod's SKU. An Azure AI Search SKU cannot be changed in place — moving from basic to
  # standard means creating a new service and reindexing — so a rehearsal on basic tests
  # a resource prod will never run.
  sku = "standard"

  # One replica, where prod runs two. Replicas buy a read SLA during the service's own
  # maintenance windows; they change no behaviour a release rehearsal exercises.
  replica_count   = 1
  partition_count = 1

  # No API keys, as everywhere. An admin key is a full-control data-plane credential that
  # survives identity revocation and cannot be attributed to a caller.
  local_authentication_enabled = false

  # Only the retrieve tool queries the index. Not the orchestrator.
  reader_principal_ids = {
    retrieve = module.identity.identities[local.tool_identity_names["retrieve"]].principal_id
  }

  # Schema and corpus management is a deploy-time grant held by the deploying principal,
  # not by any workload. Nothing that answers questions can rewrite what it retrieves.
  service_contributor_principal_ids = {
    deployer = data.azurerm_client_config.current.object_id
  }
  contributor_principal_ids = {
    deployer = data.azurerm_client_config.current.object_id
  }

  # Prod's conditional, unchanged, and the reason this environment runs EP1 plans. Supply
  # the DNS zone IDs and the public endpoint closes; omit them and it stays open. Testing
  # the private path here is the single most valuable thing staging does, because a
  # private endpoint without a working zone resolves to the public IP from inside the
  # VNet and every resource still reports healthy.
  public_network_access_enabled = var.knowledge_private_dns_zone_ids == null
  private_endpoint_subnet_id    = var.knowledge_private_dns_zone_ids == null ? null : module.networking.subnet_id
  private_dns_zone_ids          = var.knowledge_private_dns_zone_ids

  log_analytics_workspace_id = local.log_analytics_workspace_id

  tags = local.tags
}

module "model_integration" {
  source = "../../modules/model-integration"

  name_prefix         = local.name_prefix
  resource_group_name = module.networking.resource_group_name
  location            = var.location

  # Bring-your-own by default, as in dev and prod: an Azure OpenAI account can require
  # subscription-level access approval, which is a request Terraform cannot make.
  create_account        = var.create_openai_account
  azure_openai_endpoint = var.azure_openai_endpoint

  # Declared by all three roots and passed by none of them until 2026-08-23, which
  # meant a reader who set it in their tfvars got silence. See HARDENING-PLAN task 8.
  azure_openai_key_secret_name = var.azure_openai_key_secret_name

  model_name            = var.model_name
  model_version         = var.model_version
  model_deployment_name = var.model_deployment_name

  # Between dev's 10 and prod's 60. Enough headroom that a rehearsal is not throttled by
  # a ceiling prod would never hit, low enough to stay a ceiling.
  deployment_capacity = var.model_deployment_capacity

  create_content_filter = true

  # Inference only, and only for the reasoning tool.
  caller_principal_ids = {
    reason = module.identity.identities[local.tool_identity_names["reason"]].principal_id
  }

  log_analytics_workspace_id = local.log_analytics_workspace_id

  tags = local.tags
}

module "tools" {
  source = "../../modules/tools"

  name_prefix         = local.name_prefix
  resource_group_name = module.networking.resource_group_name
  location            = var.location
  tenant_id           = data.azurerm_client_config.current.tenant_id

  tools = var.tools

  tool_identities = {
    for name, identity_name in local.tool_identity_names :
    name => module.identity.identities[identity_name]
  }

  orchestrator_principal_id      = module.identity.identities["orchestrator"].principal_id
  approval_executor_principal_id = module.identity.identities["approval-executor"].principal_id

  common_environment = {
    KNOWLEDGE_SEARCH_SERVICE = module.knowledge.search_service_name
    KNOWLEDGE_INDEX          = module.knowledge.index_name
    STATE_STORAGE_ACCOUNT    = module.state.storage_account_name
    STATE_TABLE_NAME         = module.state.table_name
    ARCHIVE_STORAGE_ACCOUNT  = module.archive.storage_account_name
    ARCHIVE_CONTAINER        = module.archive.container_name
    KEY_VAULT_URI            = module.security.keyvault_uri
    AZURE_OPENAI_ENDPOINT    = module.model_integration.azure_openai_endpoint

    # The deployment, not a model name. On Azure OpenAI the deployment is the
    # addressable unit and it is what carries the RAI content filter.
    MODEL_DEPLOYMENT = module.model_integration.model_deployment_name
  }

  # EP1, not dev's Y1, and this is the load-bearing line of the whole environment. Y1
  # cannot join a VNet, so on Consumption the private endpoints above are unreachable and
  # the thing staging exists to verify cannot be verified. It is also the largest single
  # cost here; see the note on service_plan_sku in variables.tf.
  service_plan_sku = var.function_service_plan_sku

  # LRS rather than prod's ZRS — durability, not behaviour.
  storage_replication_type = "LRS"

  # Off, as in prod. Nothing legitimate uses the storage account keys; every caller
  # authenticates as itself. This is where you find out something did.
  storage_shared_access_key_enabled = false

  tags = local.tags
}

module "approval" {
  source = "../../modules/approval"

  name_prefix         = local.name_prefix
  resource_group_name = module.networking.resource_group_name
  location            = var.location
  tenant_id           = data.azurerm_client_config.current.tenant_id

  validator_identity = module.identity.identities["approval-validator"]
  executor_identity  = module.identity.identities["approval-executor"]

  orchestrator_principal_id = module.identity.identities["orchestrator"].principal_id
  approver_principal_ids    = var.approver_principal_ids

  validator_package_path = var.approval_validator.package_path
  executor_package_path  = var.approval_executor.package_path

  validator_environment = var.approval_validator.environment

  executor_environment = merge(var.approval_executor.environment, {
    WRITE_TOOL_URLS = jsonencode(module.tools.write_tool_urls)

    WRITE_TOOL_AUDIENCES = jsonencode({
      for name, audience in module.tools.tool_audiences :
      name => audience if var.tools[name].access == "write"
    })
  })

  common_environment = {
    KEY_VAULT_URI = module.security.keyvault_uri
  }

  # Off, where prod has it on, and this is the third one-way door. Cosmos continuous
  # backup cannot be disabled once enabled — the account has to be recreated to undo it.
  # Prod accepts that trade because the approval record is the audit trail; staging's
  # approval records do not outlive the rehearsal.
  enable_continuous_backup = false

  # Premium by default, matching prod, and the second-largest cost line. Standard is the
  # cheaper choice and it is a real one — but the two are not interchangeable: a Service
  # Bus namespace cannot be upgraded from Standard to Premium in place, and Premium is
  # what supports private endpoints. Rehearsing on Standard tests a different resource
  # than the one prod runs. See the note in variables.tf before overriding.
  servicebus_sku                = var.servicebus_sku
  servicebus_capacity           = 1
  servicebus_local_auth_enabled = false

  service_plan_sku                  = var.function_service_plan_sku
  storage_replication_type          = "LRS"
  storage_shared_access_key_enabled = false

  tags = local.tags
}

module "observability" {
  source = "../../modules/observability"

  name_prefix         = local.name_prefix
  resource_group_name = module.networking.resource_group_name
  location            = var.location
  tenant_id           = data.azurerm_client_config.current.tenant_id

  # Dev-scale. Nothing in staging is investigated months later; the next release replaces
  # the evidence.
  log_retention_days = var.log_retention_days

  function_app_ids = merge(
    module.tools.function_app_ids,
    module.approval.function_app_ids,
  )

  logic_app_id = local.logic_app_id

  trace_emitter = {
    identity                  = module.identity.identities["trace-emitter"]
    package_path              = var.trace_emitter.package_path
    orchestrator_principal_id = module.identity.identities["orchestrator"].principal_id
  }

  service_plan_sku         = var.function_service_plan_sku
  storage_replication_type = "LRS"

  daily_cost_threshold_usd = var.daily_cost_threshold_usd

  # Prod's zero, not dev's five. A trace record that fails schema validation means the
  # emitter and the metric filters disagree about the record shape, and that disagreement
  # is silent — the alerts simply match nothing. Staging is where it should surface, so
  # the threshold is as strict here as in prod.
  schema_failure_threshold = 0

  alert_email_receivers   = var.alert_email_receivers
  alert_webhook_receivers = var.alert_webhook_receivers

  tags = local.tags
}

module "orchestration" {
  source = "../../modules/orchestration"

  name_prefix         = local.name_prefix
  resource_group_name = module.networking.resource_group_name
  location            = var.location

  orchestrator_identity = module.identity.identities["orchestrator"]

  read_tool_urls = module.tools.read_tool_urls
  tool_audiences = module.tools.tool_audiences

  validator_url      = module.approval.validator_url
  validator_audience = module.approval.validator_audience

  trace_emitter = {
    url      = module.observability.trace_emitter_url
    audience = module.observability.trace_emitter_audience
  }

  # Prod's budgets, deliberately not relaxed. Loosening them would let staging pass runs
  # that prod would cut off at the loop bound, which is the class of failure a release
  # rehearsal most needs to reproduce.
  max_steps        = 8
  approval_timeout = "PT4H"

  tags = local.tags
}
