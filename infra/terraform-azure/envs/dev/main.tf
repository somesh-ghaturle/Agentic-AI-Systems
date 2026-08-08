terraform {
  backend "local" {}
}

provider "azurerm" {
  features {}
}

module "networking" {
  source = "../../modules/networking"
  resource_group_name = "agentic-dev-rg"
  location = "eastus"
}

module "observability" {
  source = "../../modules/observability"
  resource_group_name = module.networking.resource_group_name
  location = "eastus"
}

module "model_integration" {
  source = "../../modules/model-integration"
  azure_openai_endpoint = ""
  azure_openai_key_secret_name = ""
}

# Example identity + security wiring for dev: creates a service principal and a Key Vault
module "identity" {
  source = "../../modules/identity"
  name_prefix = "agentic-dev"
}

module "security" {
  source = "../../modules/security"
  resource_group_name = module.networking.resource_group_name
  location = "eastus"
  tenant_id = "" # set in tfvars for prod or via environment
  name_prefix = "agentic-dev"
  service_principal_object_id = module.identity.service_principal_id
  # For a real secret, set create_model_key_secret=true and pass model_key_secret_value securely
  create_model_key_secret = false
  model_key_secret_name = "agentic-model-key"
}
