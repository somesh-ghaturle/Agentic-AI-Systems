terraform {
  required_version = ">= 1.6"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 5.0"
    }
  }
}

resource "azurerm_storage_account" "state_sa" {
  name                     = replace("${var.name_prefix}statesa", "-", "")
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = var.account_replication_type

  # Stated rather than inherited, for the same reason modules/tools states them: the
  # azurerm defaults already match, and a provider default is not a guarantee. This
  # account held execution state behind none of them while its four siblings each
  # declared all three.
  min_tls_version                 = "TLS1_2"
  https_traffic_only_enabled      = true
  allow_nested_items_to_be_public = false

  blob_properties {
    # Soft delete, not versioning. Versioning answers "what did this look like before the
    # overwrite"; this answers "the delete was a mistake, put it back" — and a delete is
    # the accident that has no other recovery path here.
    delete_retention_policy {
      days = var.soft_delete_retention_days
    }

    container_delete_retention_policy {
      days = var.soft_delete_retention_days
    }
  }

  tags = var.tags
}

resource "azurerm_storage_table" "execution_state" {
  name               = "executionstate"
  storage_account_id = azurerm_storage_account.state_sa.id
}
