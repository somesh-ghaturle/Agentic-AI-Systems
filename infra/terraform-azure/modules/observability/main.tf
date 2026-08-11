# Observability — the workspace everything logs into
#
# Only the workspace so far. What is NOT here yet, and what the AWS side does have:
# diagnostic settings routing each Function App and the Logic App into this workspace,
# and the alert rules built on the trace records (approvals abandoned, executions timing
# out, daily cost). Until those exist, this workspace collects platform metrics and
# nothing that would tell you the gate had failed. See ARCHITECTURE.md § Remaining work.

resource "azurerm_log_analytics_workspace" "law" {
  name                = "${var.name_prefix}-law"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "PerGB2018"
  retention_in_days   = var.log_retention_days

  tags = var.tags
}
