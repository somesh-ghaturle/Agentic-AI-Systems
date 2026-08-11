variable "name_prefix" {
  description = "Prefix for resource names, e.g. agentic-dev."
  type        = string
}

variable "resource_group_name" {
  description = "Resource group for the tool function apps."
  type        = string
}

variable "location" {
  description = "Azure region."
  type        = string
}

variable "tenant_id" {
  description = "Entra tenant ID. Used to build the Easy Auth issuer endpoint."
  type        = string

  validation {
    condition     = can(regex("^[0-9a-fA-F-]{36}$", var.tenant_id))
    error_message = "tenant_id must be a GUID. An empty string here silently produces an issuer URL that validates nothing."
  }
}

variable "tools" {
  description = <<-DESC
    The tools this system exposes, keyed by name.

    `access` is the load-bearing field and everything else in this module follows from
    it. Classify by what the handler DOES, not by what it is called — a tool named
    "lookup_account" that also writes an audit row is a write tool. When unsure, classify
    as write: the cost of an unnecessary gate is one extra click, the cost of a missing
    one is an irreversible action nobody authorized.
  DESC

  type = map(object({
    access        = string
    package_path  = string
    environment   = optional(map(string), {})
    max_instances = optional(number, 10)
  }))

  validation {
    condition     = alltrue([for k, v in var.tools : contains(["read", "write"], v.access)])
    error_message = "Every tool's access must be exactly 'read' or 'write'. Any other value skips the split without erroring."
  }

  validation {
    condition     = alltrue([for k, v in var.tools : fileexists(v.package_path)])
    error_message = "Every tool's package_path must exist at plan time — the zip is read to compute its hash. Run src/build.sh first."
  }
}

variable "tool_identities" {
  description = <<-DESC
    Map of tool name to its managed identity, from modules/identity. Every tool gets its
    own principal so that grants are per-tool rather than shared, matching one IAM role
    per Lambda on the AWS side.
  DESC

  type = map(object({
    id           = string
    principal_id = string
    client_id    = string
  }))
}

variable "orchestrator_principal_id" {
  description = <<-DESC
    Object ID of the orchestrator's managed identity. Receives the invoke app role on
    READ tools only. It is never granted on a write tool, which is half of why the
    orchestrator has no route to one.
  DESC
  type        = string
}

variable "approval_executor_principal_id" {
  description = <<-DESC
    Object ID of the approval executor's managed identity — the only principal granted
    the invoke app role on WRITE tools.

    Null is permitted so a read-only deployment can stand alone, but declaring a write
    tool without it trips a precondition rather than creating a tool nobody can reach.
  DESC
  type        = string
  default     = null
}

variable "common_environment" {
  description = "App settings applied to every tool, merged under each tool's own environment."
  type        = map(string)
  default     = {}
}

variable "service_plan_sku" {
  description = <<-DESC
    App Service plan SKU. Y1 is Consumption — cheap, but it cannot join a VNet, so
    private endpoints are unavailable. Prod uses an Elastic Premium SKU (EP1+) for VNet
    integration.
  DESC
  type        = string
  default     = "Y1"
}

variable "python_version" {
  description = "Python runtime for the function apps."
  type        = string
  default     = "3.12"
}

variable "storage_replication_type" {
  description = "Replication for the tools storage account. LRS in dev, GRS/ZRS in prod."
  type        = string
  default     = "LRS"
}

variable "storage_shared_access_key_enabled" {
  description = <<-DESC
    Whether the storage account accepts its shared access keys at all. False is the
    stronger posture and is what prod uses: with managed identity everywhere, nothing
    legitimate needs the key, so leaving it enabled only preserves an attack path.
  DESC
  type        = bool
  default     = true
}

variable "storage_public_network_access_enabled" {
  description = <<-DESC
    Whether the storage account is reachable from the internet.

    Setting this false requires a private endpoint to already exist, or Terraform itself
    loses the data plane and container/table operations fail mid-apply. Left true by
    default for that reason — see ARCHITECTURE.md for what remains before prod can close
    it.
  DESC
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags applied to every resource in this module."
  type        = map(string)
  default     = {}
}
