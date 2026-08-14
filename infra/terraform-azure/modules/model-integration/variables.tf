variable "create_account" {
  type        = bool
  description = <<-DESC
    Whether Terraform creates the Azure OpenAI account, deployment, and content filter.

    False — the default — is bring-your-own: pass `azure_openai_endpoint` and
    `model_deployment_name` for an account provisioned out of band, and this module creates
    nothing. That is the honest default because an Azure OpenAI account can require
    subscription-level access approval, and a module that always creates one fails to apply
    in a tenant that has not been granted it.

    True provisions the whole model layer, including the content filter that is this tree's
    equivalent of the Bedrock guardrail in terraform-aws/modules/security. Prefer it once
    the subscription is enrolled: with `create_account = false` there is nothing in
    Terraform asserting that a content filter exists at all.
  DESC
  default     = false
}

variable "name_prefix" {
  type        = string
  description = "Prefix for resource names, typically \"<project>-<env>\". Also becomes the custom subdomain, which must be globally unique."
  default     = ""
}

variable "resource_group_name" {
  type        = string
  description = "Resource group for the account. Required when create_account is true."
  default     = null
}

variable "location" {
  type        = string
  description = "Region for the account. Model availability varies by region more than most Azure services — a deployment can fail for a model that exists elsewhere."
  default     = null
}

variable "sku_name" {
  type        = string
  description = "Cognitive account SKU. S0 is the only tier Azure OpenAI offers."
  default     = "S0"
}

variable "local_auth_enabled" {
  type        = bool
  description = <<-DESC
    Whether the account accepts API keys.

    Leave this false. Every other credential in this tree is a managed identity precisely so
    there is nothing to leak, rotate, or account for in a blast-radius analysis; an account
    key is a portal-visible credential that survives identity revocation and cannot be
    attributed to a caller after the fact.
  DESC
  default     = false
}

variable "allow_local_auth_acknowledged" {
  type        = bool
  description = "Set true to confirm that enabling API keys is deliberate. The precondition on the account refuses local_auth_enabled without it, so the choice appears in the diff rather than in a default nobody revisited."
  default     = false
}

variable "public_network_access_enabled" {
  type        = bool
  description = "Whether the account answers on its public endpoint. IAM is the control either way; this closes the network route."
  default     = true
}

# ---------------------------------------------------------------------------
# The deployment
# ---------------------------------------------------------------------------

variable "model_name" {
  type        = string
  description = "Model to deploy, e.g. gpt-4o. Availability is region-specific."
  default     = "gpt-4o"
}

variable "model_version" {
  type        = string
  description = "Model version. Pinned rather than floating: a model that changes underneath a prompt-versioned reasoning step makes results non-reproducible, and nothing in the trace record would attribute the change."
  default     = "2024-11-20"
}

variable "model_deployment_name" {
  type        = string
  description = "Deployment name the reasoning tool targets. Created when create_account is true; passed through untouched when it is false."
  default     = "reasoning"
}

variable "deployment_sku_name" {
  type        = string
  description = "Deployment SKU. `Standard` is pay-per-token; `ProvisionedManaged` reserves throughput and bills for it whether or not you use it."
  default     = "Standard"
}

variable "deployment_capacity" {
  type        = number
  description = <<-DESC
    Throughput in thousands of tokens per minute.

    This is the closest thing to a spend ceiling the model layer has. An agent stuck in a
    retry loop hits this before it hits the daily cost alarm, which only fires after the
    money is spent — so a modest value here is a cheaper control than the alarm watching it.
  DESC
  default     = 10

  validation {
    condition     = var.deployment_capacity > 0
    error_message = "deployment_capacity must be positive. A zero-capacity deployment accepts no requests."
  }
}

variable "version_upgrade_option" {
  type        = string
  description = "What happens when Azure retires the pinned model version. `NoAutoUpgrade` fails loudly instead of silently moving the deployment underneath a versioned prompt."
  default     = "NoAutoUpgrade"

  validation {
    condition     = contains(["NoAutoUpgrade", "OnceNewDefaultVersionAvailable", "OnceCurrentVersionExpired"], var.version_upgrade_option)
    error_message = "version_upgrade_option must be NoAutoUpgrade, OnceNewDefaultVersionAvailable, or OnceCurrentVersionExpired."
  }
}

# ---------------------------------------------------------------------------
# The content filter — this tree's guardrail
# ---------------------------------------------------------------------------

variable "create_content_filter" {
  type        = bool
  description = <<-DESC
    Whether to create a Responsible AI policy and attach it to the deployment.

    A mitigation layer, not the control — the same status terraform-aws gives its Bedrock
    guardrail. It catches a meaningful share of injection attempts cheaply, and a determined
    injection will get past it, which is exactly why the write path is gated separately.

    Note what it does NOT do: Azure RAI policies have no PII filter. `aws_bedrock_guardrail`
    masks PII entities at the model boundary as a backstop for what upstream masking misses;
    there is no equivalent to attach to a deployment here, so on this tree that masking is
    entirely a property of handler code.
  DESC
  default     = true
}

variable "base_policy_name" {
  type        = string
  description = "Microsoft-managed policy this one builds on. Named explicitly so an Azure-side default change shows up as a diff rather than being absorbed silently."
  default     = "Microsoft.DefaultV2"
}

variable "content_filters" {
  type = list(object({
    name               = string
    enabled            = bool
    block              = bool
    severity_threshold = optional(string)
    source             = string
  }))

  description = <<-DESC
    Filters in the policy. `source` is "Prompt" or "Completion" — a category has to be
    listed once for each direction you want it filtered, which is the mistake worth watching
    for: a prompt-only list leaves model output unfiltered.

    `severity_threshold` is the level at and above which the filter acts: Low, Medium, or
    High. It does not apply to the `Jailbreak` and `Protected Material` filters, which are
    detections rather than graded severities.
  DESC

  default = [
    { name = "Hate", enabled = true, block = true, severity_threshold = "Medium", source = "Prompt" },
    { name = "Hate", enabled = true, block = true, severity_threshold = "Medium", source = "Completion" },
    { name = "Sexual", enabled = true, block = true, severity_threshold = "Medium", source = "Prompt" },
    { name = "Sexual", enabled = true, block = true, severity_threshold = "Medium", source = "Completion" },
    { name = "Violence", enabled = true, block = true, severity_threshold = "Medium", source = "Prompt" },
    { name = "Violence", enabled = true, block = true, severity_threshold = "Medium", source = "Completion" },
    { name = "Selfharm", enabled = true, block = true, severity_threshold = "Medium", source = "Prompt" },
    { name = "Selfharm", enabled = true, block = true, severity_threshold = "Medium", source = "Completion" },

    # The one that matters most for an agentic system: prompt-injection detection on input.
    # Retrieved documents reach the model as data and can carry text phrased as
    # instructions. This catches some of that. It does not catch all of it, which is why the
    # write path is gated rather than filtered.
    { name = "Jailbreak", enabled = true, block = true, source = "Prompt" },
  ]

  validation {
    condition     = alltrue([for f in var.content_filters : contains(["Prompt", "Completion"], f.source)])
    error_message = "Each filter's source must be \"Prompt\" or \"Completion\"."
  }

  validation {
    # The null guard is an `if` clause on the comprehension, not a `||` in front of
    # `contains`. Terraform does not reliably short-circuit `||` — through 1.9.x both
    # operands are evaluated, so `f.severity_threshold == null || contains(...)` still calls
    # `contains` with a null and fails with "argument must not be null". Newer versions do
    # short-circuit, which is worse: the expression works locally and breaks in CI.
    #
    # Filtering first means `contains` is only ever reached for a filter that set the field.
    # Jailbreak and Protected Material legitimately leave it unset — they are detections
    # rather than graded severities.
    condition = alltrue([
      for f in var.content_filters : contains(["Low", "Medium", "High"], f.severity_threshold)
      if f.severity_threshold != null
    ])
    error_message = "severity_threshold must be Low, Medium, or High when set."
  }
}

# ---------------------------------------------------------------------------
# Access and wiring
# ---------------------------------------------------------------------------

variable "caller_principal_ids" {
  type        = map(string)
  description = "Principal object IDs granted `Cognitive Services OpenAI User`, keyed by a readable name. The reasoning tool's identity — inference only, no deployment management, so a compromised tool cannot remove the filter in front of it."
  default     = {}
}

variable "log_analytics_workspace_id" {
  type        = string
  description = "Workspace for RequestResponse and Audit logs. Without them a filtered request is indistinguishable from a broken one."
  default     = null
}

variable "azure_openai_endpoint" {
  type        = string
  description = "Endpoint of an account provisioned out of band. Used only when create_account is false. Empty leaves the reasoning tool without a model."
  default     = ""
}

variable "azure_openai_key_secret_name" {
  type        = string
  description = "Key Vault secret name holding a model API key, for a bring-your-own account that only accepts key auth. Prefer managed identity; this exists because not every pre-existing account has the custom subdomain that token auth requires."
  default     = ""
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to created resources."
  default     = {}
}
