# Tenant root — applied once, not per environment.
#
# Everything else in this tree is per-environment: dev and prod each build their own
# resource group, their own Function Apps, their own workspace. This root is different,
# and the difference is not stylistic.
#
# `azurerm_monitor_aad_diagnostic_setting` is scoped to the Entra tenant. There is one
# Entra tenant behind both environments. If dev and prod each managed this object, every
# `terraform apply` in one environment would revert the other's, and the two states would
# disagree permanently while both reporting success.
#
# It also needs permissions the environment roots should not have:
#
#   - Contributor at `/providers/Microsoft.aadiam`
#   - assigned by someone holding User Access Administrator at root scope
#   - Entra ID P1 or P2 on the tenant (AuditLogs export is not a Free-tier feature)
#
# Making a dev deploy require all three would be a bad trade, so this root is separated:
# different state, different credentials, different cadence. It is applied when the
# tenant changes, which is rarely, by someone who already holds those roles.
#
# ---------------------------------------------------------------------------
# Wiring
#
# This root does not read prod's state — no remote state data source, no dependency
# between the two. The two values it needs are passed in as variables, taken from prod's
# outputs by hand:
#
#     cd ../prod && terraform output -raw log_analytics_workspace_id
#     cd ../prod && terraform output -raw action_group_id
#
# That is deliberate. A remote state data source here would make a tenant-level control
# fail whenever prod's state was mid-apply or relocated, and this is the one control that
# should keep working when other things are broken.
# ---------------------------------------------------------------------------

terraform {
  # Separate state from dev and prod, deliberately. This root's objects have a different
  # lifecycle and a different blast radius; sharing state would let a routine environment
  # apply touch a tenant-level security control.
  #
  # backend "azurerm" {
  #   resource_group_name  = "<tf-state-rg>"
  #   storage_account_name = "<tfstatesa>"
  #   container_name       = "tfstate"
  #   key                  = "agentic/tenant.tfstate"
  #   use_azuread_auth     = true
  # }
  backend "local" {}
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

provider "azuread" {}

module "entra_audit" {
  source = "../../modules/entra-audit"

  name_prefix = var.name_prefix

  # The alert rule is an ordinary ARM resource and needs somewhere to live. Prod's group
  # is the right home: it is where the workspace already is, and co-locating them means
  # the alert cannot outlive the workspace it queries.
  resource_group_name = var.resource_group_name
  location            = var.location

  log_analytics_workspace_id = var.log_analytics_workspace_id
  action_group_id            = var.action_group_id

  capture_service_principal_signins = var.capture_service_principal_signins

  tags = merge(var.tags, {
    scope = "tenant"

    # Marks this as not belonging to any one environment. Someone cleaning up dev should
    # not find this in a tag query and assume it is theirs to delete.
    managed_by = "envs/tenant"
  })
}
