# Identity — user-assigned managed identities, and no credentials anywhere
#
# This module previously created an Entra application, a service principal, and a
# service principal *password* with a one-year expiry. That password lived in Terraform
# state in plaintext, had to be rotated by hand, and would have taken the system down
# silently on its first birthday. It has been removed.
#
# A user-assigned managed identity is the Azure analogue of an AWS IAM role: Azure holds
# the credential, rotates it, and never shows it to you or to the workload. There is
# nothing to leak, nothing to store, and nothing to expire.
#
# ---------------------------------------------------------------------------
# Why this module exists at all, when terraform-aws has no `identity` module
# ---------------------------------------------------------------------------
#
# On AWS the roles live in the modules that own the resources, and the tools ↔ approval
# dependency cycle is broken by computing ARNs deterministically in `locals`. Azure has
# no equivalent trick — a managed identity's principal ID is server-assigned and cannot
# be predicted before creation.
#
# So the cycle is broken by extraction instead: this module depends on nothing, and both
# `tools` and `approval` consume identities from it. Without it you get
#
#   tools → needs the executor's principal ID (to scope the app role assignment)
#   approval → needs the write tool app IDs (to invoke them)
#
# which Terraform correctly refuses to resolve.

resource "azurerm_user_assigned_identity" "this" {
  for_each = var.identities

  name                = "${var.name_prefix}-${each.key}"
  resource_group_name = var.resource_group_name
  location            = var.location

  tags = var.tags
}
