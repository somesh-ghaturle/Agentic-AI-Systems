variable "resource_group_name" {
  type        = string
  description = "Name of the resource group."
}

variable "location" {
  type        = string
  description = "Azure region."
}

variable "name_prefix" {
  type        = string
  description = "Prefix for naming resources, typically \"<project>-<env>\"."
}

variable "index_name" {
  type        = string
  description = <<-DESC
    Name of the index the retrieve tool queries.

    Terraform does not create the index — there is no `azurerm_search_index` resource — so
    this is a name the module publishes rather than a name it enforces. It must match the
    `name` field in index-schema.json and the index actually applied over the REST API. A
    mismatch fails at query time, not at apply time.
  DESC
  default     = "knowledge"
}

variable "sku" {
  type        = string
  description = <<-DESC
    Search service SKU. `free` is a shared instance with a 50MB index cap and no SLA —
    useful for a first apply, not for anything that needs to answer reliably. `basic` is the
    smallest tier with a real SLA and supports replicas.

    The SKU cannot be changed in place: moving from basic to standard destroys and recreates
    the service, taking the index with it.
  DESC
  default     = "basic"

  validation {
    condition     = contains(["free", "basic", "standard", "standard2", "standard3", "storage_optimized_l1", "storage_optimized_l2"], var.sku)
    error_message = "sku must be one of: free, basic, standard, standard2, standard3, storage_optimized_l1, storage_optimized_l2."
  }
}

variable "replica_count" {
  type        = number
  description = <<-DESC
    Replicas serving the index. One replica means no read SLA and a service that stops
    answering during its own maintenance — Azure requires 2 for a read SLA and 3 for a
    read/write SLA.

    Defaults to 1 because that is the only value the free and basic-with-one-partition
    cases accept, and a default that fails to apply is worse than a modest one. Raise it in
    prod.
  DESC
  default     = 1

  validation {
    condition     = var.replica_count >= 1 && var.replica_count <= 12
    error_message = "replica_count must be between 1 and 12."
  }
}

variable "partition_count" {
  type        = number
  description = "Partitions dividing the index. Governs index size and write throughput, not availability. Must be 1, 2, 3, 4, 6, or 12."
  default     = 1

  validation {
    condition     = contains([1, 2, 3, 4, 6, 12], var.partition_count)
    error_message = "partition_count must be 1, 2, 3, 4, 6, or 12 — the service rejects other values."
  }
}

variable "local_authentication_enabled" {
  type        = bool
  description = <<-DESC
    Whether the service issues admin and query API keys.

    Leave this false. An admin key is a full-control data-plane credential that appears in
    the portal, survives identity revocation, and cannot be attributed to a caller after the
    fact. With it false, the role assignments in this module are the only route to the index
    and the audit trail names the identity that queried it.

    Set true only when something that genuinely cannot use Entra auth has to reach the
    index, and treat that as a temporary state.
  DESC
  default     = false
}

variable "public_network_access_enabled" {
  type        = bool
  description = "Whether the service answers on its public endpoint. Set false only alongside a private endpoint, or nothing can reach the index."
  default     = true
}

variable "reader_principal_ids" {
  type        = map(string)
  description = <<-DESC
    Principal object IDs granted `Search Index Data Reader`, keyed by a readable name.

    This is the retrieve tool's identity — NOT the orchestrator's. The orchestrator never
    talks to AI Search directly; granting it access here is the natural mistake and leaves
    the retrieve tool broken.
  DESC
  default     = {}
}

variable "contributor_principal_ids" {
  type        = map(string)
  description = "Principal object IDs granted `Search Index Data Contributor` — permitted to write documents into the corpus. Deploy-time principals, not the query path. A workload that only answers questions has no reason to hold this."
  default     = {}
}

variable "service_contributor_principal_ids" {
  type        = map(string)
  description = "Principal object IDs granted `Search Service Contributor` — permitted to create and modify the index definition itself. Needed to apply index-schema.json. Strictly larger than writing documents."
  default     = {}
}

variable "private_endpoint_subnet_id" {
  type        = string
  description = "Subnet for a private endpoint onto the search service. Null skips the endpoint entirely, which is what the dev environment does."
  default     = null
}

variable "private_dns_zone_ids" {
  type        = list(string)
  description = <<-DESC
    Private DNS zone IDs (`privatelink.search.windows.net`) to register the endpoint in.

    Null creates the endpoint without DNS, which resolves the service name to its public IP
    from inside the VNet — traffic leaves the network and the endpoint sits unused while
    every resource reports healthy. Supply this whenever the subnet is set.
  DESC
  default     = null
}

variable "log_analytics_workspace_id" {
  type        = string
  description = "Workspace for OperationLogs and metrics. Query logs are how a cross-tenant retrieval bug is found after the fact; without them the evidence is gone as soon as the response is returned."
  default     = null
}

variable "tags" {
  type        = map(string)
  description = "Tags to apply to resources."
  default     = {}
}
