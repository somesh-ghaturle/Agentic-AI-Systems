# Security — the Key Vault, and who is allowed to read out of it
#
# Two things changed here from the original scaffold, both because the original was
# unsafe rather than merely incomplete.
#
# 1. Access policies were replaced with RBAC.
#
#    A vault access policy is a list attached to the vault itself. It is not visible to
#    `az role assignment list`, it does not appear in a subscription-wide access review,
#    and it cannot be scoped below the whole vault. RBAC assignments are ordinary Azure
#    role assignments: they show up everywhere access is audited, and "Key Vault Secrets
#    User" grants read on secrets without granting the ability to write or delete them.
#    The old policy here handed out Get/List/Set/Delete in one block — every caller could
#    overwrite the model key.
#
# 2. Purge protection is on by default.
#
#    With it off, a deleted vault (or a deleted secret) is gone for good the moment
#    someone runs purge, accidentally or otherwise. With it on, soft-deleted material
#    survives the retention window and can be recovered. It is left switchable only
#    because a dev vault you cannot tear down for 7 days is genuinely annoying — so dev
#    turns it off deliberately, and prod does not.
#
# Note on naming: the vault name is global across Azure, not scoped to the subscription.
# A second team deploying with the same name_prefix collides at apply time. See
# ARCHITECTURE.md § Remaining work — the same applies to every storage account in this
# stack.

data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "kv" {
  name                = "${var.name_prefix}-kv"
  location            = var.location
  resource_group_name = var.resource_group_name
  tenant_id           = var.tenant_id
  sku_name            = var.sku_name

  # See the note above. Off is a deliberate dev-only choice.
  purge_protection_enabled   = var.purge_protection_enabled
  soft_delete_retention_days = var.soft_delete_retention_days

  # Role assignments below do nothing unless this is true — with access policies in
  # force, an RBAC grant is simply ignored and every read comes back 403.
  rbac_authorization_enabled = true

  public_network_access_enabled = var.public_network_access_enabled

  network_acls {
    # Deny by default. `bypass = "AzureServices"` is what lets the Function Apps resolve
    # their Key Vault references; without it, closing public access also closes the only
    # path the workloads use.
    default_action = var.public_network_access_enabled ? "Allow" : "Deny"
    bypass         = "AzureServices"
  }

  tags = var.tags
}

# ---------------------------------------------------------------------------
# Who may read secrets
#
# One assignment per principal rather than one shared grant, so that removing a
# workload's access is a single targeted destroy and never touches anyone else's.
# ---------------------------------------------------------------------------

resource "azurerm_role_assignment" "secret_reader" {
  for_each = var.secret_reader_principal_ids

  scope                = azurerm_key_vault.kv.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = each.value
}

# ---------------------------------------------------------------------------
# Optional model key
#
# Terraform's own principal has no standing access to a vault under RBAC — being the
# creator of a resource grants nothing on its data plane. Without this assignment the
# secret below fails with a 403 on the first apply, which reads as a permissions bug in
# the pipeline rather than what it is.
# ---------------------------------------------------------------------------

resource "azurerm_role_assignment" "deployer_secrets_officer" {
  count = var.create_model_key_secret ? 1 : 0

  scope                = azurerm_key_vault.kv.id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = data.azurerm_client_config.current.object_id
}

resource "azurerm_key_vault_secret" "model_key" {
  count = var.create_model_key_secret ? 1 : 0

  name         = var.model_key_secret_name
  value        = var.model_key_secret_value
  key_vault_id = azurerm_key_vault.kv.id

  # RBAC assignments are eventually consistent. Terraform considers the role assignment
  # created before Key Vault's data plane has seen it, so without this the first apply
  # races and intermittently 403s.
  depends_on = [azurerm_role_assignment.deployer_secrets_officer]

  lifecycle {
    precondition {
      condition     = var.model_key_secret_value != ""
      error_message = "create_model_key_secret is true but model_key_secret_value is empty. That would store an empty string as the model key and fail at runtime instead of at apply."
    }
  }
}
