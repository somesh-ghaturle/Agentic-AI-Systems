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

# ---------------------------------------------------------------------------
# Model layer
#
# Azure OpenAI accounts are not created here: provisioning one requires tenant-level
# enrollment that Terraform cannot request. Create it out of band and pass the endpoint.
# ---------------------------------------------------------------------------

variable "azure_openai_endpoint" {
  description = "Azure OpenAI endpoint, e.g. https://my-openai.openai.azure.com/. Empty leaves the reasoning tool without a model."
  type        = string
  default     = ""
}

variable "azure_openai_key_secret_name" {
  description = "Key Vault secret name holding the model API key, when the deployment uses key auth rather than managed identity."
  type        = string
  default     = ""
}

variable "model_deployment_name" {
  description = "Azure OpenAI deployment name the reasoning tool targets."
  type        = string
  default     = ""
}
