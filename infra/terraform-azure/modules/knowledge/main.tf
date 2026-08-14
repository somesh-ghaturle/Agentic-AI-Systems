# Knowledge layer — Azure AI Search.
#
# The retrieve tool searches this index. The property that matters is not that retrieval
# works; it is that retrieval is tenant-scoped, and that the scoping happens *during* the
# search rather than after it.
#
# From terraform-aws/ARCHITECTURE.md section 7:
#
#   "Retrieval is tenant-scoped — enforced by CODE: filter inside the kNN clause, not
#    beside it. If it breaks: ranks other tenants' documents first, then hides them."
#
# On AI Search the mechanism is `vectorFilterMode` on the vector query. It takes two
# values and the difference between them is exactly the AWS mistake in different words:
#
#   preFilter  — the filter restricts the candidate set before the ANN traversal. Correct.
#   postFilter — the search finds k neighbours across the whole index, then discards the
#                ones the caller may not read. Two consequences, both bad: the search
#                ranked another tenant's documents to decide they were closest, and a
#                caller whose k nearest all belong to someone else gets an empty result
#                rather than their own next-best match.
#
# preFilter is the API default, which makes this the one variant of this bug that is
# introduced only by writing it out explicitly and wrongly. That is not much comfort:
# `vectorFilterMode: postFilter` reads like a performance knob, and the failure it causes
# is silent and looks like sparse data.
#
# Terraform cannot enforce that. The service below is capable of it either way. This
# comment is here because the capability and the correct use of it are different things,
# and the module that provides the first should say so.
#
# ---------------------------------------------------------------------------
# What this module does NOT create, and why
# ---------------------------------------------------------------------------
#
# The index schema. There is no `azurerm_search_index` resource and there never has been —
# the azurerm provider manages the search *service* and stops at the data plane. The index
# is created over the REST API or an SDK.
#
# That is a real gap, not a stylistic one, because the index schema is where the
# tenant-scoping story is actually decided: `tenant_id` must be `filterable` or the filter
# the retrieve tool sends is rejected at query time. A schema that omits it deploys fine
# and fails on the first real search.
#
# So the schema lives beside this file as `index-schema.json`, and HOW-TO-DEPLOY.md has the
# curl that applies it. The `Search Service Contributor` assignment below is what lets a
# deploy principal do that.
# ---------------------------------------------------------------------------

resource "azurerm_search_service" "knowledge" {
  name                = "${var.name_prefix}-search"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = var.sku

  # Partitions divide the index; replicas serve it. Neither had a variable before, so both
  # environments ran one of each regardless of SKU — a prod search service with no replica
  # redundancy, silently.
  replica_count   = var.replica_count
  partition_count = var.partition_count

  # ---------------------------------------------------------------------------
  # No API keys
  #
  # AI Search issues admin and query keys by default, and they are the reason this setting
  # matters more here than it looks. An admin key is a full-control credential on the data
  # plane that appears in the portal, survives identity revocation, and cannot be
  # attributed to a caller after the fact. The retrieve tool already has a managed
  # identity; a key would be a second, worse way in.
  #
  # With this false, `Search Index Data Reader` below is the only route to the index, and
  # the audit trail names the identity that queried it.
  # ---------------------------------------------------------------------------
  local_authentication_enabled = var.local_authentication_enabled

  # Only consulted when local auth is on. `http403` refuses an unauthenticated request
  # outright rather than returning 401 and inviting a retry with a key.
  authentication_failure_mode = var.local_authentication_enabled ? "http403" : null

  # With a private endpoint attached, the public path is dead weight that still answers.
  public_network_access_enabled = var.public_network_access_enabled

  # System-assigned so the service can reach a customer-managed key and any
  # identity-authenticated data source without a stored credential of its own.
  identity {
    type = "SystemAssigned"
  }

  tags = merge(var.tags, {
    Component = "ai-search"
    Layer     = "knowledge"
  })

  lifecycle {
    precondition {
      condition     = var.sku != "free" || (var.replica_count == 1 && var.partition_count == 1)
      error_message = "The free SKU supports exactly one replica and one partition. Either drop both to 1 or move to basic/standard."
    }

    precondition {
      condition     = var.sku != "basic" || var.partition_count == 1
      error_message = "The basic SKU supports one partition (replicas may go to 3). Use standard or above for more."
    }

    # A public-only service with local auth disabled is fine. A private-only service with
    # local auth *enabled* is the combination worth catching: it reads as the locked-down
    # option while leaving an admin key valid for anything that reaches the endpoint.
    precondition {
      condition     = var.public_network_access_enabled || !var.local_authentication_enabled
      error_message = "public_network_access_enabled is false but local_authentication_enabled is true. Network isolation is not a substitute for removing the admin key — anything inside the network still gets full data-plane control. Set local_authentication_enabled = false."
    }
  }
}

# ---------------------------------------------------------------------------
# Who may read the index
#
# This grant belongs to the *retrieve tool's* identity, not the orchestrator's. The
# orchestrator never talks to AI Search directly.
#
# The AWS tree makes the same point about OpenSearch Serverless data access policies and
# the GCP tree about `roles/aiplatform.user`, and it is worth repeating in all three
# because the mistake is natural: the orchestrator is the thing that "does retrieval" from
# a reader's point of view, so granting it access feels right and leaves the retrieve tool
# broken with an authorization error nobody expects.
#
# `Search Index Data Reader` is query-only. It cannot create, modify, or delete an index,
# and it cannot read the service's keys — so a compromised retrieve tool can read the
# corpus it was always able to read and cannot alter what anyone else retrieves. Data
# *Contributor* would allow poisoning the corpus, which is the supply-chain version of
# prompt injection and considerably harder to notice.
# ---------------------------------------------------------------------------

resource "azurerm_role_assignment" "index_reader" {
  for_each = var.reader_principal_ids

  scope                = azurerm_search_service.knowledge.id
  role_definition_name = "Search Index Data Reader"
  principal_id         = each.value
}

# The principals permitted to apply `index-schema.json` and to load documents. Separate
# from the readers on purpose: writing the corpus is a deploy-time action, and a workload
# that only answers questions has no reason to hold it.
resource "azurerm_role_assignment" "index_contributor" {
  for_each = var.contributor_principal_ids

  scope                = azurerm_search_service.knowledge.id
  role_definition_name = "Search Index Data Contributor"
  principal_id         = each.value
}

# Schema management — creating and updating the index definition itself, which is a
# control-plane operation and a strictly larger grant than writing documents.
resource "azurerm_role_assignment" "service_contributor" {
  for_each = var.service_contributor_principal_ids

  scope                = azurerm_search_service.knowledge.id
  role_definition_name = "Search Service Contributor"
  principal_id         = each.value
}

# ---------------------------------------------------------------------------
# Private endpoint
#
# Optional because it is the one piece of this module that needs a subnet, and requiring
# one would make the knowledge layer undeployable in the flat-network setup the dev
# environment uses.
#
# When enabled, the service is reachable over the VNet. Note what this does and does not
# buy: it removes the public route, and it changes nothing about authorization. Anything
# inside the VNet still needs a role assignment above.
# ---------------------------------------------------------------------------

resource "azurerm_private_endpoint" "knowledge" {
  count = var.private_endpoint_subnet_id == null ? 0 : 1

  name                = "${var.name_prefix}-search-pe"
  resource_group_name = var.resource_group_name
  location            = var.location
  subnet_id           = var.private_endpoint_subnet_id

  private_service_connection {
    name                           = "${var.name_prefix}-search-psc"
    private_connection_resource_id = azurerm_search_service.knowledge.id
    subresource_names              = ["searchService"]

    # Manual approval would leave the endpoint pending until someone clicks through the
    # portal, which in practice means a deploy that reports success and a tool that cannot
    # reach the index.
    is_manual_connection = false
  }

  # Without a private DNS zone the service name still resolves to its public IP from inside
  # the VNet, so traffic leaves the network and the endpoint sits unused while appearing
  # healthy. Supplying the zone is what makes the private path actually the path.
  dynamic "private_dns_zone_group" {
    for_each = var.private_dns_zone_ids == null ? [] : [var.private_dns_zone_ids]
    content {
      name                 = "${var.name_prefix}-search-dns"
      private_dns_zone_ids = private_dns_zone_group.value
    }
  }

  tags = merge(var.tags, {
    Component = "ai-search"
    Layer     = "knowledge"
  })
}

# ---------------------------------------------------------------------------
# Diagnostics
#
# Query logs are how a cross-tenant retrieval bug is found after the fact. Without them,
# the evidence that a filter was missing is gone as soon as the response is returned.
# ---------------------------------------------------------------------------

resource "azurerm_monitor_diagnostic_setting" "knowledge" {
  count = var.log_analytics_workspace_id == null ? 0 : 1

  name                       = "${var.name_prefix}-search-diag"
  target_resource_id         = azurerm_search_service.knowledge.id
  log_analytics_workspace_id = var.log_analytics_workspace_id

  enabled_log {
    category = "OperationLogs"
  }

  enabled_metric {
    category = "AllMetrics"
  }
}
