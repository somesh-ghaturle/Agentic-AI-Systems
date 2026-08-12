variable "project_id" {
  description = "GCP project."
  type        = string
}

variable "name_prefix" {
  description = "Prefix for resource names, typically \"<project>-<env>\"."
  type        = string
}

variable "location" {
  description = "KMS location. Must be a region that can host the resources encrypted with this key — a key in `us-central1` cannot encrypt a bucket in `europe-west1`."
  type        = string
}

variable "rotation_period" {
  description = "Automatic key rotation period, as a duration string in seconds (e.g. \"7776000s\" for 90 days). Rotation creates a new primary version; existing data stays readable under the version that encrypted it."
  type        = string
  default     = "7776000s"
}

variable "protection_level" {
  description = "SOFTWARE or HSM. HSM costs meaningfully more per key version and per operation; it buys a hardware-backed key that never exists in software form."
  type        = string
  default     = "SOFTWARE"

  validation {
    condition     = contains(["SOFTWARE", "HSM"], var.protection_level)
    error_message = "protection_level must be SOFTWARE or HSM."
  }
}

variable "decrypter_members" {
  description = "Workload principals granted cryptoKeyDecrypter, keyed by name. For handlers that decrypt payloads themselves, as distinct from services that encrypt on your behalf."
  type        = map(string)
  default     = {}
}

variable "create_model_key_secret" {
  description = "Create a Secret Manager secret for a model API key. Off by default: Claude on Vertex AI uses the caller's service account, so there is usually no key to store."
  type        = bool
  default     = false
}

variable "secret_reader_members" {
  description = "Principals granted secretAccessor on the model key secret, keyed by name. Ignored when create_model_key_secret is false."
  type        = map(string)
  default     = {}
}

variable "labels" {
  description = "Labels applied to every resource in this module that supports them."
  type        = map(string)
  default     = {}
}
