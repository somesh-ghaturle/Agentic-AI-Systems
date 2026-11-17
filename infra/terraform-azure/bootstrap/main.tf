# Remote state bootstrap — the storage account the environment roots keep their state in.
#
# Every root under envs/ declares `backend "local" {}` until its `backend "azurerm"` block
# is swapped in, and that block needs a storage account and a container to point at. This
# root creates them. It is applied once per subscription, before any environment, and it is
# the one root whose own state stays local: an account cannot hold the state that records
# its own creation. Keep that local state file somewhere backed up, or re-import the three
# resources if it is lost — three, not the dozens an environment root would need.
#
# Nothing here is part of the agent. No module depends on it and the write boundary does
# not pass through it. It is a root of its own, with its own resource group, so that an
# environment root can never destroy the account holding its own state.
#
# The azurerm backend locks with a blob lease, so there is nothing else to create.

terraform {
  required_version = ">= 1.6"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 5.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

data "azurerm_client_config" "current" {}

resource "azurerm_resource_group" "state" {
  name     = "${var.project}-tfstate-rg"
  location = var.location

  tags = local.tags
}

locals {
  tags = {
    Project   = var.project
    ManagedBy = "terraform"
    Component = "terraform-state"
  }
}

resource "azurerm_storage_account" "state" {
  # Globally unique, 3-24 lowercase alphanumerics. `storage_account_suffix` is what makes
  # it unique: `<project>tfstate` alone is taken by whoever copied this tree first.
  name                     = "${replace(var.project, "-", "")}tfstate${var.storage_account_suffix}"
  resource_group_name      = azurerm_resource_group.state.name
  location                 = azurerm_resource_group.state.location
  account_tier             = "Standard"
  account_replication_type = var.account_replication_type

  min_tls_version                 = "TLS1_2"
  https_traffic_only_enabled      = true
  allow_nested_items_to_be_public = false

  # The backend block uses `use_azuread_auth = true`, so nothing needs the account keys.
  # With them off, read access to state is an RBAC grant that shows up in an access
  # review, not possession of a key.
  shared_access_key_enabled = false

  blob_properties {
    # The recovery path. A corrupted or truncated state file is restored from the previous
    # version, which only exists if versioning was on before the bad write.
    versioning_enabled = true

    delete_retention_policy {
      days = var.soft_delete_retention_days
    }

    container_delete_retention_policy {
      days = var.soft_delete_retention_days
    }
  }

  # State is the one thing in this subscription that cannot be rebuilt from the
  # configuration. Removing this line is the deliberate act a `destroy` should require.
  lifecycle {
    prevent_destroy = true
  }

  tags = local.tags
}

resource "azurerm_storage_container" "state" {
  name                  = "tfstate"
  storage_account_id    = azurerm_storage_account.state.id
  container_access_type = "private"
}

# Data-plane access for whoever applies this root. Owning the subscription does not grant
# it: with shared keys off, reading or writing a state blob needs this role explicitly.
# Grant the same role to every other principal that runs Terraform against the trees.
resource "azurerm_role_assignment" "state_writer" {
  scope                = azurerm_storage_account.state.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}
