# Dev environment.
#
# Cheaper and more permissive than prod, with the differences confined to variables
# rather than to structure. The wiring below is identical to prod — that is the point. An
# approval gate you only exercise in prod is an approval gate you have not tested.
#
# What differs in dev: Consumption plans instead of Elastic Premium, Standard Service Bus
# instead of Premium, no PITR on the approval records, no purge protection on the vault,
# no WORM policy on the archive, and storage shared keys left enabled.
#
# ---------------------------------------------------------------------------
# How the two cycles are broken, because the wiring looks indirect on purpose
# ---------------------------------------------------------------------------
#
# **Cycle 1: tools ↔ approval.** modules/tools needs the executor's principal ID to scope
# its write-tool app role assignment; the executor needs the write tools' addresses to
# call them.
#
# On AWS this is broken by computing ARNs in `locals` — resource names are deterministic,
# so the ARNs are too. That does not work for Azure principals: a managed identity's
# principal ID is server-assigned and cannot be predicted before creation.
#
# So it is broken by extraction. modules/identity depends on nothing and creates every
# principal up front; tools, approval, orchestration, and the trace emitter all consume
# identities from it rather than from each other.
#
# **Cycle 2: orchestration ↔ observability.** The workflow calls the trace emitter, which
# lives in observability; observability needs the workflow's resource ID for its
# diagnostic setting and failure alert.
#
# This one DOES yield to the AWS trick, because ARM resource IDs — unlike principal IDs —
# are fully determined by subscription, resource group, and name. `local.logic_app_id`
# below is that constructed value.
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
  name_prefix         = "${var.project}-dev"
  resource_group_name = "${var.project}-dev-rg"

  # Managed identity names become Azure resource names, so they are lowercase with
  # hyphens only. Tool names may carry underscores (they are also Python module names),
  # which is why this normalizes rather than interpolating the tool name directly.
  tool_identity_names = { for name in keys(var.tools) : name => "tool-${replace(name, "_", "-")}" }

  # One principal per workload. The alternative — a shared identity — makes every grant
  # in this stack a grant to everything, which is the thing the read/write split exists
  # to prevent.
  identity_names = toset(concat(
    ["orchestrator", "approval-validator", "approval-executor", "trace-emitter"],
    values(local.tool_identity_names),
  ))

  # Cycle-breaker. See the note at the top of this file: this is the ID the workflow will
  # have, known before it exists because ARM IDs are deterministic.
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
    Environment = "dev"
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

  # Dev traces are not evidence. Expire them, and do NOT lock them — a container nobody
  # can empty is a dev environment nobody can tear down.
  transition_cool_days     = 7
  transition_archive_days  = 30
  expiration_days          = 90
  immutability_period_days = null

  tags = local.tags
}

module "knowledge" {
  source = "../../modules/knowledge"

  name_prefix         = local.name_prefix
  resource_group_name = module.networking.resource_group_name
  location            = var.location
  sku                 = "basic"

  # One of each in dev. No read SLA, and the service stops answering during its own
  # maintenance — acceptable when the alternative is paying for redundancy nobody is
  # relying on. prod runs 2 replicas.
  replica_count   = 1
  partition_count = 1

  # No API keys, in dev too. A dev admin key is a real credential against a real service,
  # and the habit of having one is what puts one in prod.
  local_authentication_enabled = false

  # Only the retrieve tool queries the index. Not the orchestrator — it never talks to AI
  # Search directly, and granting it here is the natural mistake that leaves the retrieve
  # tool broken.
  reader_principal_ids = {
    retrieve = module.identity.identities[local.tool_identity_names["retrieve"]].principal_id
  }

  # Whoever applies index-schema.json and loads the corpus. In dev that is the operator
  # running terraform, which is why the deploying principal appears here and nowhere else.
  service_contributor_principal_ids = {
    deployer = data.azurerm_client_config.current.object_id
  }
  contributor_principal_ids = {
    deployer = data.azurerm_client_config.current.object_id
  }

  # Public endpoint in dev — a private endpoint needs a DNS zone this environment does not
  # create. IAM is still the control either way.
  public_network_access_enabled = true
  private_endpoint_subnet_id    = null

  log_analytics_workspace_id = local.log_analytics_workspace_id

  tags = local.tags
}

module "model_integration" {
  source = "../../modules/model-integration"

  name_prefix         = local.name_prefix
  resource_group_name = module.networking.resource_group_name
  location            = var.location

  # Bring-your-own by default: an Azure OpenAI account can require subscription-level
  # access approval, and a dev root that cannot apply in an unenrolled tenant is a dev root
  # nobody can use. Set create_openai_account = true once the subscription is enrolled —
  # until then nothing here asserts that a content filter exists at all.
  create_account        = var.create_openai_account
  azure_openai_endpoint = var.azure_openai_endpoint

  model_name            = var.model_name
  model_version         = var.model_version
  model_deployment_name = var.model_deployment_name

  # Low on purpose. Throughput is the cheapest ceiling on a runaway agent — it bites before
  # the daily cost alarm, which only fires after the money is spent.
  deployment_capacity = 10

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

  service_plan_sku = "Y1"

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

  # Opens approvals; never resolves them.
  orchestrator_principal_id = module.identity.identities["orchestrator"].principal_id

  # Resolves approvals; the only principals that can. Empty means nobody can approve
  # anything — safe, but every gated action will sit until its window closes.
  approver_principal_ids = var.approver_principal_ids

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

# Depends on tools and approval for the apps it must route to. Uses the CONSTRUCTED
# workflow ID rather than reading it off the orchestration module — see the note at the
# top of this file.
module "observability" {
  source = "../../modules/observability"

  name_prefix         = local.name_prefix
  resource_group_name = module.networking.resource_group_name
  location            = var.location
  tenant_id           = data.azurerm_client_config.current.tenant_id

  # The floor Log Analytics accepts. Dev traces are not evidence.
  log_retention_days = 30

  # Must be complete. An app missing here drops out of every alert query silently.
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

  # Low on purpose. In dev this is a runaway-loop detector, not a budget.
  daily_cost_threshold_usd = 25
  schema_failure_threshold = 5

  alert_email_receivers = var.alert_email_receivers

  tags = local.tags
}

module "orchestration" {
  source = "../../modules/orchestration"

  name_prefix         = local.name_prefix
  resource_group_name = module.networking.resource_group_name
  location            = var.location

  # Must be the same identity modules/tools granted the read-tool invoke role to, above.
  orchestrator_identity = module.identity.identities["orchestrator"]

  # Read tools only. Write tool URLs are not in this output at all, so the workflow has
  # no address to call even before Entra refuses it a token.
  read_tool_urls = module.tools.read_tool_urls
  tool_audiences = module.tools.tool_audiences

  validator_url      = module.approval.validator_url
  validator_audience = module.approval.validator_audience

  trace_emitter = {
    url      = module.observability.trace_emitter_url
    audience = module.observability.trace_emitter_audience
  }

  # Generous in dev: a reviewer who is not watching should not fail a test run.
  max_steps        = 12
  approval_timeout = "PT24H"

  tags = local.tags
}
