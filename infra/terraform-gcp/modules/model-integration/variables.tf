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
