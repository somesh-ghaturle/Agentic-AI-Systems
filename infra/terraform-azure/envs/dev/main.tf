terraform {
  backend "local" {}
}

provider "azurerm" {
  features {}
}

locals {
  name_prefix = "agentic-dev"
  location    = "eastus"

  tags = {
    Project     = "agentic-system"
    Environment = "dev"
    ManagedBy   = "terraform"
  }
}

module "networking" {
  source              = "../../modules/networking"
  resource_group_name = "agentic-dev-rg"
  location            = local.location
  name_prefix         = local.name_prefix
}

module "observability" {
  source              = "../../modules/observability"
  resource_group_name = module.networking.resource_group_name
  location            = local.location
  name_prefix         = local.name_prefix
}

module "model_integration" {
  source                       = "../../modules/model-integration"
  azure_openai_endpoint        = ""
  azure_openai_key_secret_name = ""
}

module "identity" {
  source      = "../../modules/identity"
  name_prefix = local.name_prefix
}

module "security" {
  source                      = "../../modules/security"
  resource_group_name         = module.networking.resource_group_name
  location                    = local.location
  tenant_id                   = "" # set in tfvars or environment
  name_prefix                 = local.name_prefix
  service_principal_object_id = module.identity.service_principal_id
  create_model_key_secret     = false
  model_key_secret_name       = "agentic-model-key"
}

module "state" {
  source              = "../../modules/state"
  resource_group_name = module.networking.resource_group_name
  location            = local.location
  name_prefix         = local.name_prefix
  tags                = local.tags
}

module "archive" {
  source              = "../../modules/archive"
  resource_group_name = module.networking.resource_group_name
  location            = local.location
  name_prefix         = local.name_prefix
  tags                = local.tags
}

module "knowledge" {
  source              = "../../modules/knowledge"
  resource_group_name = module.networking.resource_group_name
  location            = local.location
  name_prefix         = local.name_prefix
  sku                 = "standard"
  tags                = local.tags
}

module "tools" {
  source              = "../../modules/tools"
  resource_group_name = module.networking.resource_group_name
  location            = local.location
  name_prefix         = local.name_prefix
  common_environment = {
    "KNOWLEDGE_SEARCH_SERVICE" = module.knowledge.search_service_name
    "STATE_TABLE_NAME"         = module.state.table_name
  }
  tags = local.tags
}

module "approval" {
  source              = "../../modules/approval"
  resource_group_name = module.networking.resource_group_name
  location            = local.location
  name_prefix         = local.name_prefix
  tags                = local.tags
}

module "orchestration" {
  source              = "../../modules/orchestration"
  resource_group_name = module.networking.resource_group_name
  location            = local.location
  name_prefix         = local.name_prefix
  tags                = local.tags
}
