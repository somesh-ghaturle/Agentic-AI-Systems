# Prod environment.
#
# Structurally identical to dev — same modules, same wiring, same order. Every difference
# is a variable value, and they are all in one direction: longer retention, backups on,
# shared keys off, WORM locked, Premium tiers where Premium is what buys network
# isolation.
#
# See envs/dev/main.tf for how the two dependency cycles are broken. The reasoning is the
# same here and is not repeated.

terraform {
  # Local state is not acceptable for prod. Two operators applying at once corrupt each
  # other's work and there is no lock to stop them. Fill this in before the first apply.
  #
  # backend "azurerm" {
  #   resource_group_name  = "<tf-state-rg>"
  #   storage_account_name = "<tfstatesa>"
  #   container_name       = "tfstate"
  #   key                  = "agentic/prod.tfstate"
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
  name_prefix         = "${var.project}-prod"
  resource_group_name = "${var.project}-prod-rg"

  tool_identity_names = { for name in keys(var.tools) : name => "tool-${replace(name, "_", "-")}" }

  identity_names = toset(concat(
    ["orchestrator", "approval-validator", "approval-executor", "trace-emitter"],
    values(local.tool_identity_names),
  ))

  logic_app_id = "/subscriptions/${var.subscription_id}/resourceGroups/${local.resource_group_name}/providers/Microsoft.Logic/workflows/${local.name_prefix}-orchestrator"

  # The same cycle-breaker, for the same reason, on a third edge.
  #
  # modules/knowledge wants the workspace for its OperationLogs diagnostic setting, and
  # reading it from `module.observability` would close a loop:
  #
  #   knowledge → observability → tools → knowledge
  #
  # (tools consumes the search service name; observability consumes the tools' app IDs.)
  # A workspace ARM ID is deterministic in the same way the Logic App's is, so it is
  # constructed here rather than read back.
  log_analytics_workspace_id = "/subscriptions/${var.subscription_id}/resourceGroups/${local.resource_group_name}/providers/Microsoft.OperationalInsights/workspaces/${local.name_prefix}-law"

  tags = {
    Project     = var.project
    Environment = "prod"
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

  # Both deliberate and both irreversible in practice: a purge-protected vault cannot be
  # destroyed on a whim, which is exactly the property wanted for the thing holding
  # production credentials.
  purge_protection_enabled   = true
  soft_delete_retention_days = 90

  create_model_key_secret = false

  tags = local.tags
}

module "state" {
  source = "../../modules/state"

  name_prefix         = local.name_prefix
  resource_group_name = module.networking.resource_group_name
  location            = var.location

  # Zone-redundant: execution state is what an in-flight run resumes from, so losing a
  # zone should not lose the runs.
  account_replication_type = "ZRS"

  tags = local.tags
}

module "archive" {
  source = "../../modules/archive"

  name_prefix         = local.name_prefix
  resource_group_name = module.networking.resource_group_name
  location            = var.location

  # Geo-redundant, and kept for seven years. This is the trace archive — the evidence
  # trail behind every decision the system made.
  account_replication_type  = "GRS"
  shared_access_key_enabled = false
  transition_cool_days      = 30
  transition_archive_days   = 90
  expiration_days           = 2555

  # WORM, LOCKED. Read modules/archive/variables.tf before changing either line.
  #
  # This is what makes the archive evidence rather than logs: while the window is open,
  # no one — including the subscription owner — can delete or overwrite a trace. The
  # consequence is that this resource group cannot be destroyed for seven years. That is
  # the same commitment S3 Object Lock in COMPLIANCE mode makes on the AWS side, and it
  # is the point rather than a side effect.
  immutability_period_days = 2555
  lock_immutability_policy = true

  tags = local.tags
}

module "knowledge" {
  source = "../../modules/knowledge"

  name_prefix         = local.name_prefix
  resource_group_name = module.networking.resource_group_name
  location            = var.location
  sku                 = "standard"

  # Two replicas is the minimum for a read SLA. At one, the service stops answering during
  # its own maintenance and retrieval degrades for reasons no trace explains.
  replica_count   = 2
  partition_count = 1

  # No API keys. An admin key here is a full-control data-plane credential that survives
  # identity revocation and cannot be attributed to a caller, so the role assignments below
  # are the only route to the corpus.
  local_authentication_enabled = false

  # Only the retrieve tool queries the index. Not the orchestrator.
  reader_principal_ids = {
    retrieve = module.identity.identities[local.tool_identity_names["retrieve"]].principal_id
  }

  # Schema and corpus management is a deploy-time grant held by the deploying principal,
  # not by any workload. Nothing that answers questions can rewrite what it retrieves —
  # corpus poisoning is prompt injection with persistence, and considerably harder to spot.
  service_contributor_principal_ids = {
    deployer = data.azurerm_client_config.current.object_id
  }
  contributor_principal_ids = {
    deployer = data.azurerm_client_config.current.object_id
  }

  # Reachable from the VNet only. Set `private_dns_zone_ids` alongside the subnet or the
  # service name still resolves to its public IP from inside the network and the endpoint
  # sits unused while every resource reports healthy.
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

  # Bring-your-own by default, for the same reason as dev: an Azure OpenAI account can
  # require subscription-level access approval. Set create_openai_account = true once the
  # subscription is enrolled — while it is false, nothing in Terraform asserts that a
  # content filter sits in front of the model at all.
  create_account        = var.create_openai_account
  azure_openai_endpoint = var.azure_openai_endpoint

  model_name            = var.model_name
  model_version         = var.model_version
  model_deployment_name = var.model_deployment_name

  # Sized for real traffic, and still a ceiling. Throughput bites before the daily cost
  # alarm, which only fires after the money is spent.
  deployment_capacity = 60

  # The mitigation layer. Same status as the Bedrock guardrail on the AWS side: worth
  # having, and not what stops a determined injection — that is the write boundary.
  create_content_filter = true

  # Inference only, and only for the reasoning tool. Not deployment management: a
  # compromised reasoning tool can spend money and cannot remove the filter in front of it.
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
    # addressable unit and it is what carries the RAI content filter, so a handler
    # calling a bare model name bypasses nothing — it simply 404s.
    MODEL_DEPLOYMENT = module.model_integration.model_deployment_name
  }

  # Elastic Premium, not Consumption. The reason is not performance: Y1 cannot join a
  # VNet, so every private endpoint in this stack is unreachable from a Consumption plan.
  # Prod pays for EP1 to keep that door open.
  service_plan_sku         = "EP1"
  storage_replication_type = "ZRS"

  # Nothing legitimate uses the storage account keys — every caller authenticates as
  # itself. Leaving them enabled would preserve an attack path with no user.
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

  # The record of who authorized what. Point-in-time restore is the difference between a
  # bad deploy being an inconvenience and being a compliance incident.
  enable_continuous_backup = true

  # Premium is what supports private endpoints and customer-managed keys. It costs
  # substantially more than Standard and that is the trade being made.
  servicebus_sku                = "Premium"
  servicebus_capacity           = 1
  servicebus_local_auth_enabled = false

  service_plan_sku                  = "EP1"
  storage_replication_type          = "ZRS"
  storage_shared_access_key_enabled = false

  tags = local.tags
}

module "observability" {
  source = "../../modules/observability"

  name_prefix         = local.name_prefix
  resource_group_name = module.networking.resource_group_name
  location            = var.location
  tenant_id           = data.azurerm_client_config.current.tenant_id

  # A year. Long enough to answer "who approved this, and on what evidence" during an
  # audit that starts months after the fact.
  log_retention_days = 365

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

  service_plan_sku         = "EP1"
  storage_replication_type = "ZRS"

  # A real budget rather than a loop detector. Tune it to the environment's actual spend
  # — set far above it and the alarm is decorative.
  daily_cost_threshold_usd = var.daily_cost_threshold_usd
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

  # Tighter than dev on both counts. A shorter approval window is deliberate: an approval
  # nobody answered for four hours is already an incident, and a longer window mostly
  # delays finding that out.
  max_steps        = 8
  approval_timeout = "PT4H"

  tags = local.tags
}
