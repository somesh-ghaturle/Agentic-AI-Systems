# Long-term archive — full traces, retained long, written once
#
# Prompt versions, model versions, tool calls with arguments and results, token counts,
# costs, latency, outcomes. Cheap to turn on now and impossible to reconstruct later.
#
# PII MASKING IS AN APPLICATION RESPONSIBILITY. Terraform cannot enforce it. Mask before
# the write, not after.
#
# ---------------------------------------------------------------------------
# Immutability, and why the lifecycle policy alone was not enough
# ---------------------------------------------------------------------------
#
# A lifecycle management policy tiers blobs to cool, then archive, then deletes them. It
# is a cost control. It does nothing to stop anyone with write access from deleting the
# evidence trail early — which is the property the AWS side gets from S3 Object Lock in
# COMPLIANCE mode.
#
# The Azure analogue is a time-based immutability policy on the container. While the
# retention window is open, blobs cannot be deleted or overwritten by anyone, including
# the subscription owner. Version-level immutability additionally requires blob
# versioning, which is enabled below so that an overwrite creates a version rather than
# destroying the record.

resource "azurerm_storage_account" "archive_sa" {
  name                = replace("${var.name_prefix}archivesa", "-", "")
  resource_group_name = var.resource_group_name
  location            = var.location

  account_tier             = "Standard"
  account_replication_type = var.account_replication_type

  min_tls_version                 = "TLS1_2"
  https_traffic_only_enabled      = true
  allow_nested_items_to_be_public = false
  shared_access_key_enabled       = var.shared_access_key_enabled

  blob_properties {
    # An overwrite must not destroy the prior record. This is the same reasoning as
    # bucket versioning on the AWS side, and it is a precondition for version-level
    # immutability.
    versioning_enabled = true

    delete_retention_policy {
      days = var.soft_delete_retention_days
    }

    container_delete_retention_policy {
      days = var.soft_delete_retention_days
    }
  }

  tags = var.tags
}

resource "azurerm_storage_container" "archive" {
  name                  = "trace-archive"
  storage_account_id    = azurerm_storage_account.archive_sa.id
  container_access_type = "private"
}

# ---------------------------------------------------------------------------
# WORM
#
# `locked = true` is irreversible. Once locked, the policy's retention period can be
# extended but never shortened, and neither the container nor the account can be deleted
# until every blob in it has aged out. That is not a side effect to work around — it is
# the entire point, and it is what "the evidence cannot be quietly removed" means.
#
# Left unlocked by default so that a dev environment stays disposable. Prod locks it.
# ---------------------------------------------------------------------------

resource "azurerm_storage_container_immutability_policy" "archive" {
  count = var.immutability_period_days == null ? 0 : 1

  # `.id` rather than the `.resource_manager_id` this took in azurerm 3.x — since the
  # container moved to `storage_account_id`, its `id` IS the resource manager ID.
  storage_container_resource_manager_id = azurerm_storage_container.archive.id
  immutability_period_in_days           = var.immutability_period_days

  # Append-only writes stay permitted while the policy is in force. Traces are written
  # once and never edited, so this changes nothing operationally — but it is what allows
  # an in-progress multi-block upload to finish rather than failing halfway.
  protected_append_writes_all_enabled = true

  locked = var.lock_immutability_policy
}

# ---------------------------------------------------------------------------
# Cost control, distinct from the above
#
# Read-rarely data does not belong in hot storage forever. These transitions cut the cost
# of retention enough that "keep everything" stays affordable, which is the point.
#
# Note the interaction: while an immutability policy is in force, the delete action below
# cannot remove a blob before its retention window closes. The tiering still applies. If
# expiration_days is shorter than immutability_period_days, deletion simply does not
# happen until the later date — Terraform will not warn about this, so the precondition
# on the variable does.
# ---------------------------------------------------------------------------

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

      # Versions exist because versioning is on above. Without a rule for them, every
      # overwritten trace keeps a hot-tier version forever and the archive quietly costs
      # far more than the lifecycle policy suggests.
      version {
        delete_after_days_since_creation = var.expiration_days
      }
    }
  }
}
