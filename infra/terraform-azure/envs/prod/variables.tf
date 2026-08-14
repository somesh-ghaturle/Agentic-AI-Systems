variable "project" {
  description = "Project name. Combined with the environment to prefix every resource."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9-]{1,10}$", var.project))
    error_message = "project must be lowercase alphanumeric/hyphens and at most 10 chars, so \"<project>-prod-approvals\" stays within Azure's 24-char Cosmos and storage account name limits."
  }
}

variable "subscription_id" {
  description = <<-DESC
    Subscription to deploy into. Required as of azurerm 4.x — the provider no longer
    infers it from the Azure CLI context, and omitting it fails at plan with a message
    that does not say so.
  DESC
  type        = string

  validation {
    condition     = can(regex("^[0-9a-fA-F-]{36}$", var.subscription_id))
    error_message = "subscription_id must be a GUID."
  }
}

variable "location" {
  description = "Azure region."
  type        = string
  default     = "eastus"
}

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

variable "tools" {
  description = <<-DESC
    Tool definitions. See modules/tools/variables.tf for the full contract.

    `access` decides who may invoke each function — "read" means the orchestrator calls
    it directly, "write" means only the approval executor can. Classify by what the
    handler DOES, not by what it is called. A tool marked read that mutates state defeats
    the split, and no amount of Terraform can detect that.
  DESC

  type = map(object({
    access        = string
    package_path  = string
    environment   = optional(map(string), {})
    max_instances = optional(number, 10)
  }))

  default = {}
}

# ---------------------------------------------------------------------------
# Approval gate
# ---------------------------------------------------------------------------

variable "approval_validator" {
  description = "Validator function — deterministic ownership, permission, and limit checks that run before a human sees a proposal."

  type = object({
    package_path = string
    environment  = optional(map(string), {})
  })
}

variable "approval_executor" {
  description = <<-DESC
    Executor function — the only principal permitted to invoke write tools.

    WRITE_TOOL_URLS and WRITE_TOOL_AUDIENCES are injected by the root module; do not set
    them here.
  DESC

  type = object({
    package_path = string
    environment  = optional(map(string), {})
  })
}

variable "approver_principal_ids" {
  description = <<-DESC
    Object IDs of the users or groups permitted to resolve an approval, keyed by a name
    you choose. A group is usually right, so that adding an approver is a directory
    change rather than a Terraform apply.

    Empty means nobody can approve anything. Every gated action will sit until its window
    closes and then be recorded as abandoned — a safe failure, but still a failure.
  DESC
  type        = map(string)
  default     = {}
}

# ---------------------------------------------------------------------------
# Observability
# ---------------------------------------------------------------------------

variable "trace_emitter" {
  description = <<-DESC
    The function the orchestrator calls to write its own trace records. Source belongs
    alongside the other handlers.

    Not optional: a workflow's run history lands in a different table with a different
    shape from handler logs, so without this the loop-bound and daily-cost alerts match
    nothing — and an alert matching nothing looks exactly like a healthy system.
  DESC

  type = object({
    package_path = string
  })
}

variable "alert_email_receivers" {
  description = <<-DESC
    Map of receiver name to email address for the alert action group.

    Empty means every alert fires into the void: the rules evaluate, the portal shows
    them firing, and nobody is told. Set this before anyone depends on the environment.
  DESC
  type        = map(string)
  default     = {}
}

variable "alert_webhook_receivers" {
  description = "Map of receiver name to webhook URI, for routing alerts into an incident tool. Email alone is not a paging channel."
  type        = map(string)
  default     = {}
}

variable "daily_cost_threshold_usd" {
  description = <<-DESC
    Daily spend, in USD, above which the cost alert fires.

    Unlike dev — where the threshold is a runaway-loop detector and can be arbitrarily
    low — this needs to be tuned to what the environment actually spends. Set far above
    real spend and the alarm is decorative; set at it and the alarm is noise.
  DESC
  type        = number

  validation {
    condition     = var.daily_cost_threshold_usd > 0
    error_message = "daily_cost_threshold_usd must be positive. To disable the alert, remove it from the observability module rather than setting a threshold nothing can exceed."
  }
}

# ---------------------------------------------------------------------------
# Model layer
#
# Terraform can create the Azure OpenAI account, its deployment, and the content filter in
# front of it — but only in a subscription that has been granted access to Azure OpenAI.
# That approval is a request Terraform cannot make, so account creation is opt-in and the
# default is to point at an account provisioned out of band.
#
# While `create_openai_account` is false, note what is NOT asserted anywhere in this tree:
# that a content filter exists on the model at all. The AWS tree always creates its Bedrock
# guardrail; here that is a manual step until the switch is flipped.
# ---------------------------------------------------------------------------

variable "create_openai_account" {
  description = "Whether Terraform provisions the Azure OpenAI account, deployment, and content filter. Requires the subscription to be enrolled for Azure OpenAI. False points the reasoning tool at azure_openai_endpoint instead."
  type        = bool
  default     = false
}

variable "azure_openai_endpoint" {
  description = "Azure OpenAI endpoint, e.g. https://my-openai.openai.azure.com/. Used when create_openai_account is false. Empty leaves the reasoning tool without a model."
  type        = string
  default     = ""
}

variable "azure_openai_key_secret_name" {
  description = "Key Vault secret name holding the model API key, when a bring-your-own deployment uses key auth rather than managed identity. Prefer identity: a created account disables key auth outright."
  type        = string
  default     = ""
}

variable "model_deployment_name" {
  description = "Azure OpenAI deployment name the reasoning tool targets. Created when create_openai_account is true, passed through when it is false."
  type        = string
  default     = "reasoning"
}

variable "model_name" {
  description = "Model to deploy when create_openai_account is true. Availability is region-specific."
  type        = string
  default     = "gpt-4o"
}

variable "model_version" {
  description = "Model version, pinned. A model that moves underneath a prompt-versioned reasoning step makes results non-reproducible and nothing in the trace record explains the change."
  type        = string
  default     = "2024-11-20"
}

# ---------------------------------------------------------------------------
# Knowledge layer networking
# ---------------------------------------------------------------------------

variable "knowledge_private_dns_zone_ids" {
  description = <<-DESC
    Private DNS zone IDs for `privatelink.search.windows.net`. Supplying them puts the
    search service behind a private endpoint in the orchestration subnet and closes its
    public endpoint.

    Null leaves the service on its public endpoint. That is the default because the zone is
    usually managed centrally rather than per-environment, and a private endpoint without a
    zone is worse than no private endpoint: the service name resolves to its public IP from
    inside the VNet, so traffic leaves the network while every resource reports healthy.
  DESC
  type        = list(string)
  default     = null
}
