terraform {
  required_version = ">= 1.6"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 5.0"
    }
  }
}

# Execution state — the records an in-flight run resumes from.
#
# This used to be an `azurerm_storage_table` on a storage account, and that had no recovery
# path at all. The account's soft delete covered blobs and containers; Table Storage is a
# separate data plane in the same account with no soft delete, no versioning and no
# point-in-time restore, so a deleted or overwritten row was gone in every environment,
# prod included. docs/HOW-TO-RECOVER.md said so plainly and nothing could be turned on to
# change it.
#
# Cosmos DB adds continuous backup, which is what DynamoDB PITR gives the AWS tree and
# Firestore PITR gives the GCP one.
#
# The NoSQL API rather than the Table API, though the Table API would have kept the old
# data model. Two reasons. Key-based authentication can only be switched off on a NoSQL
# account, and data-plane RBAC is the model the approvals account already uses — so a tool
# reaches this the way the executor reaches approvals, through `shared/cosmos_io.py` and a
# role assignment, with no key in an app setting. And nothing in this tree had written to
# the old table, so there was no client to stay compatible with.
#
# A second Cosmos account rather than a container in the approvals account, on purpose. The
# approvals account is the audit trail and only the validator and executor hold a data role
# on it; putting run state beside it would mean granting every tool that resumes a run a
# role on the account that records who authorized what.

resource "azurerm_cosmosdb_account" "state" {
  name                = "${var.name_prefix}-state"
  resource_group_name = var.resource_group_name
  location            = var.location
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"

  # Serverless for the reason the approvals account is: run state is written at the pace
  # of executions, and provisioned throughput would bill for capacity nobody uses.
  capabilities {
    name = "EnableServerless"
  }

  consistency_policy {
    # A resumed run reads the state the previous step wrote, possibly from another
    # instance. Under eventual consistency it can read the step before that and repeat
    # work that already happened.
    consistency_level = "Strong"
  }

  geo_location {
    location          = var.location
    failover_priority = 0
  }

  # The recovery path. Restoring creates a new account as of a timestamp — it does not
  # repair this one in place — which is the same shape as DynamoDB and Firestore PITR.
  dynamic "backup" {
    for_each = var.enable_continuous_backup ? [1] : []
    content {
      type = "Continuous"
      tier = var.continuous_backup_tier
    }
  }

  # No account keys. Nothing reads this account yet, so there is no caller to break, and
  # the first one should arrive with a role assignment and not a connection string.
  local_authentication_enabled = false

  public_network_access_enabled     = var.public_network_access_enabled
  is_virtual_network_filter_enabled = var.public_network_access_enabled == false

  tags = var.tags
}

resource "azurerm_cosmosdb_sql_database" "state" {
  name                = "state"
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.state.name
}

resource "azurerm_cosmosdb_sql_container" "execution_state" {
  name                  = "executionstate"
  resource_group_name   = var.resource_group_name
  account_name          = azurerm_cosmosdb_account.state.name
  database_name         = azurerm_cosmosdb_sql_database.state.name
  partition_key_paths   = ["/execution_id"]
  partition_key_version = 2
}
