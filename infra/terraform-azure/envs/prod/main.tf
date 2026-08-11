# Prod environment.
#
# Structurally identical to dev — same modules, same wiring, same order. Every difference
# is a variable value, and they are all in one direction: longer retention, backups on,
# shared keys off, Premium tiers where Premium is what buys network isolation.
#
# See envs/dev/main.tf for why the identity module exists and how it breaks the
# tools ↔ approval dependency cycle. The reasoning is the same here and is not repeated.

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
  name_prefix = "${var.project}-prod"

  tool_identity_names = { for name in keys(var.tools) : name => "tool-${replace(name, "_", "-")}" }

  identity_names = toset(concat(
    ["orchestrator", "approval-validator", "approval-executor"],
    values(local.tool_identity_names),
  ))

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
  resource_group_name = "${local.name_prefix}-rg"
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

module "observability" {
  source = "../../modules/observability"

  name_prefix         = local.name_prefix
  resource_group_name = module.networking.resource_group_name
  location            = var.location

  # A year. Long enough to answer "who approved this, and on what evidence" during an
  # audit that starts months after the fact.
  log_retention_days = 365

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
  account_replication_type = "GRS"
  transition_cool_days     = 30
  transition_archive_days  = 90
  expiration_days          = 2555

  tags = local.tags
}

module "knowledge" {
  source = "../../modules/knowledge"

  name_prefix         = local.name_prefix
  resource_group_name = module.networking.resource_group_name
  location            = var.location
  sku                 = "standard"

  tags = local.tags
}

module "model_integration" {
  source = "../../modules/model-integration"

  azure_openai_endpoint        = var.azure_openai_endpoint
  azure_openai_key_secret_name = var.azure_openai_key_secret_name
  model_deployment_name        = var.model_deployment_name
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
    STATE_STORAGE_ACCOUNT    = module.state.storage_account_name
    STATE_TABLE_NAME         = module.state.table_name
    ARCHIVE_STORAGE_ACCOUNT  = module.archive.storage_account_name
    ARCHIVE_CONTAINER        = module.archive.container_name
    KEY_VAULT_URI            = module.security.keyvault_uri
    AZURE_OPENAI_ENDPOINT    = module.model_integration.azure_openai_endpoint
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

  validator_identity = module.identity.identities["approval-validator"]
  executor_identity  = module.identity.identities["approval-executor"]

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

module "orchestration" {
  source = "../../modules/orchestration"

  name_prefix         = local.name_prefix
  resource_group_name = module.networking.resource_group_name
  location            = var.location

  orchestrator_identity = module.identity.identities["orchestrator"]

  tags = local.tags
}
