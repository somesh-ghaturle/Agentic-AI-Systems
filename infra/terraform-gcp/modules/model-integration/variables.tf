variable "project_id" {
  description = "GCP project."
  type        = string
}

variable "location" {
  description = "Vertex AI region for model calls. Anthropic model availability varies by region — us-east5 and europe-west1 carry the broadest selection."
  type        = string
}

variable "model_id" {
  description = "Vertex AI model identifier the reason handler requests, e.g. \"claude-opus-4-5@20251101\". Passed to handlers as an environment variable; nothing here validates that it exists or is enabled."
  type        = string
}

variable "manage_api_enablement" {
  description = "Enable aiplatform.googleapis.com from Terraform. Set false when the project's APIs are managed elsewhere, which is common when several environments share a project."
  type        = bool
  default     = true
}

variable "model_caller_members" {
  description = "Principals granted roles/aiplatform.user, keyed by name. The reason handler needs this; nothing else should have it."
  type        = map(string)
  default     = {}
}

# ---------------------------------------------------------------------------
# The guardrail — Model Armor. See guardrail.tf for what it is and is not.
# ---------------------------------------------------------------------------

variable "name_prefix" {
  description = "Prefix for the guardrail template ID, typically \"<project>-<env>\". Template IDs take hyphens, not underscores."
  type        = string
  default     = "agentic"
}

variable "create_guardrail" {
  description = <<-EOT
    Whether to create the Model Armor template.

    A mitigation layer, not the control — the same status terraform-aws gives its Bedrock
    guardrail. It catches a meaningful share of injection attempts and PII leakage cheaply,
    and a determined injection will get past it, which is why the write path is gated
    separately.

    On by default because the failure mode of not having it is silent.
  EOT
  type        = bool
  default     = true
}

variable "guardrail_location" {
  description = "Region for the Model Armor template and floor setting. Availability is narrower than Vertex AI's; \"global\" works everywhere the service is offered."
  type        = string
  default     = "global"
}

variable "jailbreak_confidence_level" {
  description = <<-EOT
    Detection threshold for prompt injection and jailbreak attempts: LOW_AND_ABOVE,
    MEDIUM_AND_ABOVE, or HIGH_ONLY.

    LOW_AND_ABOVE is the deliberate default. It produces more false positives than the
    others, and for the input path of an agentic system that is the correct trade: a blocked
    legitimate request is a retry, and an injection that gets through is an action nobody
    intended.
  EOT
  type        = string
  default     = "LOW_AND_ABOVE"

  validation {
    condition     = contains(["LOW_AND_ABOVE", "MEDIUM_AND_ABOVE", "HIGH_ONLY"], var.jailbreak_confidence_level)
    error_message = "jailbreak_confidence_level must be LOW_AND_ABOVE, MEDIUM_AND_ABOVE, or HIGH_ONLY."
  }
}

variable "rai_filters" {
  description = "Responsible-AI content categories and the confidence at which each acts. Mirrors the content_policy_config filters on the AWS guardrail."
  type = list(object({
    filter_type      = string
    confidence_level = string
  }))

  default = [
    { filter_type = "HATE_SPEECH", confidence_level = "MEDIUM_AND_ABOVE" },
    { filter_type = "HARASSMENT", confidence_level = "MEDIUM_AND_ABOVE" },
    { filter_type = "SEXUALLY_EXPLICIT", confidence_level = "MEDIUM_AND_ABOVE" },
    { filter_type = "DANGEROUS", confidence_level = "MEDIUM_AND_ABOVE" },
  ]

  validation {
    condition = alltrue([
      for f in var.rai_filters :
      contains(["HATE_SPEECH", "HARASSMENT", "SEXUALLY_EXPLICIT", "DANGEROUS"], f.filter_type)
    ])
    error_message = "filter_type must be HATE_SPEECH, HARASSMENT, SEXUALLY_EXPLICIT, or DANGEROUS."
  }

  validation {
    condition = alltrue([
      for f in var.rai_filters :
      contains(["LOW_AND_ABOVE", "MEDIUM_AND_ABOVE", "HIGH_ONLY"], f.confidence_level)
    ])
    error_message = "confidence_level must be LOW_AND_ABOVE, MEDIUM_AND_ABOVE, or HIGH_ONLY."
  }
}

variable "sdp_mode" {
  description = <<-EOT
    Sensitive Data Protection inspection at the model boundary.

      basic    — SDP's built-in infotypes, no other resource required.
      advanced — your own DLP inspect/deidentify templates, for when "PII" means something
                 specific to your data rather than the default set.
      none     — no PII inspection. This is the state the Azure tree is permanently in,
                 because Azure RAI policies have no PII filter to attach.

    This is a backstop for what upstream masking misses, not a replacement for it.
  EOT
  type        = string
  default     = "basic"

  validation {
    condition     = contains(["basic", "advanced", "none"], var.sdp_mode)
    error_message = "sdp_mode must be basic, advanced, or none."
  }
}

variable "sdp_inspect_template" {
  description = "DLP inspect template ID. Required when sdp_mode is \"advanced\"."
  type        = string
  default     = null
}

variable "sdp_deidentify_template" {
  description = "DLP de-identify template ID, for masking rather than blocking. Optional even in advanced mode."
  type        = string
  default     = null
}

variable "create_floor_setting" {
  description = <<-EOT
    Whether to enforce the same filters on every Vertex AI call in the project, rather than
    only on calls that ask for them.

    This is the difference between a guardrail the handler chooses to use and one it cannot
    skip. Off by default because it applies to every Vertex AI call in the project including
    ones this tree did not create — which is exactly the reach that makes it effective and
    exactly why it should not switch itself on in a shared project.
  EOT
  type        = bool
  default     = false
}

variable "floor_setting_block" {
  description = "True blocks what the filters catch. False logs what it would have blocked and blocks nothing — a rollout position, not a destination. A floor setting left in inspect-only mode reads as enabled in the console and stops nothing."
  type        = bool
  default     = true
}

variable "labels" {
  description = "Labels applied to the guardrail template."
  type        = map(string)
  default     = {}
}
