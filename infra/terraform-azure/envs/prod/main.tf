terraform {
  backend "local" {}
}

provider "azurerm" {
  features {}
}

module "networking" {
  source = "../../modules/networking"
  resource_group_name = "agentic-prod-rg"
  location = "eastus"
  name_prefix = "agentic-prod"
}

module "security" {
  source = "../../modules/security"
  resource_group_name = module.networking.resource_group_name
  location = "eastus"
  tenant_id = ""
}

module "observability" {
  source = "../../modules/observability"
  resource_group_name = module.networking.resource_group_name
  location = "eastus"
}
