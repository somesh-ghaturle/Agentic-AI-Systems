# Orchestration — the Logic App the orchestrator runs as
#
# The workflow definition itself is not yet written; this creates the workflow and, more
# importantly, attaches the identity that the rest of the stack has already been built
# around. modules/tools grants the invoke app role on every READ tool to
# `orchestrator_principal_id`. If that identity is never attached to anything, the grant
# names a principal that does no work and the split it describes is fiction.
#
# So the identity is attached here even while the definition is empty. What remains is
# the workflow body: call the retrieve tool, call the model step, call the validator, and
# suspend on the approval callback. See ARCHITECTURE.md § Remaining work.
#
# Why a Logic App and not Durable Functions: the AWS side suspends the run on a Step
# Functions task token, and the only Azure primitive with the same shape — a run parked
# indefinitely on an external callback, with the state machine persisted by the platform
# rather than by handler code — is a Logic App webhook action.

resource "azurerm_logic_app_workflow" "orchestrator" {
  name                = "${var.name_prefix}-orchestrator"
  location            = var.location
  resource_group_name = var.resource_group_name

  identity {
    type         = "UserAssigned"
    identity_ids = [var.orchestrator_identity.id]
  }

  tags = var.tags
}
