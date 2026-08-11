# Dev environment.
#
# Cheaper and more permissive than prod, with the differences confined to variables
# rather than to structure. The wiring below is identical to prod — that is the point. An
# approval gate you only exercise in prod is an approval gate you have not tested.
#
# What differs in dev: Consumption plans instead of Elastic Premium, Standard Service Bus
# instead of Premium, no PITR on the approval records, no purge protection on the vault,
# and storage shared keys left enabled.
#
# ---------------------------------------------------------------------------
# How the cycle is broken, because the wiring looks indirect on purpose
# ---------------------------------------------------------------------------
#
# The enforcement flow is inherently circular: the orchestrator invokes read tools, the
# executor invokes write tools, and modules/tools needs both callers' principal IDs to
# scope its app role assignments. Wired literally:
#
#     tools -> approval -> tools
#
# On AWS this is broken by computing ARNs in `locals` — the names are deterministic, so
# the ARNs are too. Azure has no equivalent: a managed identity's principal ID is
# server-assigned and cannot be predicted before creation.
#
# So it is broken by extraction instead. modules/identity depends on nothing and creates
# every principal up front; tools, approval, and orchestration all consume identities
# from it rather than from each other. That is the only reason an `identity` module
# exists here when terraform-aws has none.
# ---------------------------------------------------------------------------

terraform {
  # Local state is fine for one operator experimenting. It is not fine for anything
  # shared: two people applying at once corrupt each other's work, and there is no lock
  # to stop them. Fill this in before a second person touches the environment.
  #
  # backend "azurerm" {
  #   resource_group_name  = "<tf-state-rg>"
  #   storage_account_name = "<tfstatesa>"
  #   container_name       = "tfstate"
  #   key                  = "agentic/dev.tfstate"
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
  name_prefix = "${var.project}-dev"

  # Managed identity names become Azure resource names, so they are lowercase with
  # hyphens only. Tool names may carry underscores (they are also Python module names),
  # which is why this normalizes rather than interpolating the tool name directly.
  tool_identity_names = { for name in keys(var.tools) : name => "tool-${replace(name, "_", "-")}" }

  # One principal per workload. The alternative — a shared identity — makes every grant
  # in this stack a grant to everything, which is the thing the read/write split exists
  # to prevent.
  identity_names = toset(concat(
    ["orchestrator", "approval-validator", "approval-executor"],
    values(local.tool_identity_names),
  ))

  tags = {
    Project     = var.project
    Environment = "dev"
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

# Depends on nothing, and everything with a principal depends on it. See the note at the
# top of this file.
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

  # The floor Log Analytics accepts. Dev traces are not evidence.
  log_retention_days = 30

  tags = local.tags
}

module "security" {
  source = "../../modules/security"

  name_prefix         = local.name_prefix
  resource_group_name = module.networking.resource_group_name
  location            = var.location
  tenant_id           = data.azurerm_client_config.current.tenant_id

  # Every workload here resolves Key Vault references through its own identity, so every
  # workload needs read on secrets. Keyed by identity name so that removing one workload
  # destroys exactly one assignment.
  secret_reader_principal_ids = {
    for name, identity in module.identity.identities : name => identity.principal_id
  }

  # Off in dev only, so a torn-down environment can be recreated the same afternoon
  # instead of waiting out the retention window. Prod does not do this.
  purge_protection_enabled   = false
  soft_delete_retention_days = 7

  # Unnecessary when the model layer authenticates by managed identity, which is the
  # intended path. Set this true only if you are wiring a key-based provider.
  create_model_key_secret = false

  tags = local.tags
}

module "state" {
  source = "../../modules/state"

  name_prefix         = local.name_prefix
  resource_group_name = module.networking.resource_group_name
  location            = var.location

  tags = local.tags
}

module "archive" {
  source = "../../modules/archive"

  name_prefix         = local.name_prefix
  resource_group_name = module.networking.resource_group_name
  location            = var.location

  # Dev traces are not evidence. Expire them.
  transition_cool_days    = 7
  transition_archive_days = 30
  expiration_days         = 90

  tags = local.tags
}

module "knowledge" {
  source = "../../modules/knowledge"

  name_prefix         = local.name_prefix
  resource_group_name = module.networking.resource_group_name
  location            = var.location
  sku                 = "basic"

  tags = local.tags
}

module "model_integration" {
  source = "../../modules/model-integration"

  azure_openai_endpoint        = var.azure_openai_endpoint
  azure_openai_key_secret_name = var.azure_openai_key_secret_name
  model_deployment_name        = var.model_deployment_name
}

# The tool layer. Read tools are invoked by the orchestrator; write tools only by the
# approval executor. That split is enforced inside the module by an Entra app role, not
# by convention here.
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

  # The two halves of the split, and the only two principals that get an invoke role.
  orchestrator_principal_id      = module.identity.identities["orchestrator"].principal_id
  approval_executor_principal_id = module.identity.identities["approval-executor"].principal_id

  # Names, not endpoints. Handlers resolve endpoints from these at cold start; passing
  # resolved endpoints would pull knowledge and state into the tools dependency chain for
  # no benefit.
  common_environment = {
    KNOWLEDGE_SEARCH_SERVICE = module.knowledge.search_service_name
    STATE_STORAGE_ACCOUNT    = module.state.storage_account_name
    STATE_TABLE_NAME         = module.state.table_name
    ARCHIVE_STORAGE_ACCOUNT  = module.archive.storage_account_name
    ARCHIVE_CONTAINER        = module.archive.container_name
    KEY_VAULT_URI            = module.security.keyvault_uri
    AZURE_OPENAI_ENDPOINT    = module.model_integration.azure_openai_endpoint
  }

  service_plan_sku = "Y1"

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

  # The executor learns write tool addresses here and nowhere else. It is the only module
  # given them — module.tools.write_tool_urls has exactly one consumer by design, and a
  # second one appearing is a signal that something other than the executor intends to
  # call a write tool.
  executor_environment = merge(var.approval_executor.environment, {
    WRITE_TOOL_URLS = jsonencode(module.tools.write_tool_urls)

    # Audiences for the write tools only. The executor requests a token per audience;
    # handing it the read tools' audiences would let it call those too, which is not its
    # job even though it would be harmless.
    WRITE_TOOL_AUDIENCES = jsonencode({
      for name, audience in module.tools.tool_audiences :
      name => audience if var.tools[name].access == "write"
    })
  })

  common_environment = {
    KEY_VAULT_URI = module.security.keyvault_uri
  }

  # Dev approval records are throwaway. Prod turns this on — it is the record of who
  # authorized what.
  enable_continuous_backup = false

  servicebus_sku   = "Standard"
  service_plan_sku = "Y1"

  tags = local.tags
}

module "orchestration" {
  source = "../../modules/orchestration"

  name_prefix         = local.name_prefix
  resource_group_name = module.networking.resource_group_name
  location            = var.location

  # Must be the same identity modules/tools granted the read-tool invoke role to, above.
  orchestrator_identity = module.identity.identities["orchestrator"]

  tags = local.tags
}
