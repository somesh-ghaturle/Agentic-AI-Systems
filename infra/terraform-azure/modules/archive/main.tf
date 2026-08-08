resource "azurerm_storage_account" "archive_sa" {
  name                     = replace("${var.name_prefix}archivesa", "-", "")
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = var.account_replication_type

  tags = var.tags
}

resource "azurerm_storage_container" "archive" {
  name                  = "trace-archive"
  storage_account_id    = azurerm_storage_account.archive_sa.id
  container_access_type = "private"
}

resource "azurerm_storage_management_policy" "lifecycle" {
  storage_account_id = azurerm_storage_account.archive_sa.id

  rule {
    name    = "tier-and-expire"
    enabled = true
    filters {
      prefix_match = ["trace-archive/"]
      blob_types   = ["blockBlob"]
    }
    actions {
      base_blob {
        tier_to_cool_after_days_since_modification_greater_than    = var.transition_cool_days
        tier_to_archive_after_days_since_modification_greater_than = var.transition_archive_days
        delete_after_days_since_modification_greater_than          = var.expiration_days
      }
    }
  }
}
