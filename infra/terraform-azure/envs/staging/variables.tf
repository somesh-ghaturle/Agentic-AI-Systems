variable "project" {
  description = "Project name. Combined with the environment to prefix every resource."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9-]{1,7}$", var.project))
    error_message = "project must be lowercase alphanumeric/hyphens and at most 7 chars. Storage account names strip hyphens and cap at 24, and the longest is \"<project>stagingapprovalsa\" — \"staging\" is three characters longer than \"prod\", so a project name that is valid in envs/prod can be invalid here. Shorten the project rather than the environment."
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
  description = "Azure region. Use prod's — region changes which SKUs and model versions exist, so a rehearsal elsewhere can pass on capacity prod does not have."
  type        = string
  default     = "eastus"
}

# ---------------------------------------------------------------------------
# Cost controls
#
# The two variables below are the expensive half of staging, and both default to prod's
# value rather than dev's. That is deliberate, and it is the one place where this
# environment is not the cheap option — so the reasoning is spelled out rather than
# buried in a module call.
# ---------------------------------------------------------------------------

variable "function_service_plan_sku" {
  description = <<-DESC
    Service plan SKU for the tool, approval, and trace-emitter Function Apps.

    EP1 by default, matching prod, because Y1 (Consumption) cannot join a VNet. On Y1
    every private endpoint in this stack is unreachable and the private networking path —
    the main thing staging exists to verify — cannot be exercised at all.

    Setting this to "Y1" makes staging much cheaper and reduces it to a second dev
    environment. That is a legitimate choice on a repository nobody is deploying yet; it
    is not a legitimate choice for an environment gating a prod release.
  DESC
  type        = string
  default     = "EP1"

  validation {
    condition     = can(regex("^(Y1|EP[123])$", var.function_service_plan_sku))
    error_message = "Must be Y1 or EP1/EP2/EP3."
  }
}

variable "servicebus_sku" {
  description = <<-DESC
    Service Bus SKU for the approval gate's namespace.

    Premium by default, matching prod. Standard costs an order of magnitude less and the
    approval gate works on it — but the two are not the same resource: a namespace cannot
    be upgraded from Standard to Premium in place, and Premium is what supports private
    endpoints. A rehearsal on Standard therefore tests something prod will not run, and
    the migration itself goes untested.

    Override to "Standard" knowingly, and expect the private-endpoint half of the
    approval path to be unverified when you do.
  DESC
  type        = string
  default     = "Premium"

  validation {
    condition     = contains(["Standard", "Premium"], var.servicebus_sku)
    error_message = "Must be Standard or Premium. Basic has no topics and the approval gate needs them."
  }
}

variable "model_deployment_capacity" {
  description = "Azure OpenAI deployment capacity, in thousands of tokens per minute. Between dev's 10 and prod's 60: enough that a rehearsal is not throttled by a ceiling prod would never hit, low enough to remain a ceiling on a runaway agent."
  type        = number
  default     = 20
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
    you choose.

    Point this at a staging approver group rather than the prod one. Whether approvals
    reach a human is part of what a rehearsal verifies, but rehearsing against the real
    approver rotation trains those people to click through prompts that do not matter.

    Empty means nobody can approve anything. Every gated action will sit until its window
    closes and then be recorded as abandoned — a safe failure, but still a failure, and
    one that makes a staging run look like a gate defect.
  DESC
  type        = map(string)
  default     = {}
}

# ---------------------------------------------------------------------------
# Observability
# ---------------------------------------------------------------------------

variable "trace_emitter" {
  description = <<-DESC
    The function the orchestrator calls to write its own trace records.

    Not optional: a workflow's run history lands in a different table with a different
    shape from handler logs, so without this the loop-bound and daily-cost alerts match
    nothing — and an alert matching nothing looks exactly like a healthy system. That
    failure mode is the reason staging runs the same strict schema threshold prod does.
  DESC

  type = object({
    package_path = string
  })
}

variable "alert_email_receivers" {
  description = "Map of receiver name to email address for the alert action group. Send these to a staging channel: alert routing is worth rehearsing, but paging the on-call for a rehearsal teaches people to ignore the alert."
  type        = map(string)
  default     = {}
}

variable "alert_webhook_receivers" {
  description = "Map of receiver name to webhook URI, for routing alerts into an incident tool. Email alone is not a paging channel."
  type        = map(string)
  default     = {}
}

variable "daily_cost_threshold_usd" {
  description = "Daily spend, in USD, above which the cost alert fires. Lower than prod because staging load is a rehearsal — a day that costs this much here is a runaway loop rather than growth."
  type        = number
  default     = 50

  validation {
    condition     = var.daily_cost_threshold_usd > 0
    error_message = "daily_cost_threshold_usd must be positive. To disable the alert, remove it from the observability module rather than setting a threshold nothing can exceed."
  }
}

# ---------------------------------------------------------------------------
# Retention
#
# Dev-scale. Retention buys the ability to investigate something later, and nothing in
# staging is investigated later.
# ---------------------------------------------------------------------------

variable "log_retention_days" {
  description = "Log Analytics retention. Thirty days rather than prod's year."
  type        = number
  default     = 30
}

variable "archive_expiration_days" {
  description = "Days before archived traces are deleted. Unlike prod, which keeps them for seven years as evidence, this must be finite — an environment rebuilt every release must not accumulate an archive nothing expires."
  type        = number
  default     = 90

  validation {
    condition     = var.archive_expiration_days != null && var.archive_expiration_days > 0
    error_message = "staging must expire its trace archive. Indefinite retention is a prod decision made from a records policy; staging has no such policy and no reader for old traces."
  }
}

# Deliberately absent: immutability_period_days and lock_immutability_policy.
#
# Prod sets both, committing its resource group for seven years. They are not exposed here
# because a locked immutability policy cannot be shortened or removed by anyone — a single
# tfvars line would permanently strand the storage account of the one environment whose
# value depends on being destroyable. modules/archive receives null and false in main.tf.
#
# Also deliberately absent: any switch for Cosmos continuous backup or Key Vault purge
# protection, for the same reason. Both are one-way doors in Azure.

# ---------------------------------------------------------------------------
# Model layer
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
  description = "Model to deploy when create_openai_account is true. Availability is region-specific. Match prod: a rehearsal against a different model measures a different system."
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

    Supply them here. Null is the prod default because the zone is usually managed
    centrally, but leaving it null in staging skips the exact rehearsal this environment
    pays EP1 plans to perform: a private endpoint without a working zone resolves to the
    public IP from inside the VNet, so traffic leaves the network while every resource
    reports healthy. That is a silent failure, and the only cheap place to find it is here.
  DESC
  type        = list(string)
  default     = null
}
