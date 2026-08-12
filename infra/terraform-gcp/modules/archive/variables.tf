variable "project_id" {
  description = "GCP project."
  type        = string
}

variable "name_prefix" {
  description = "Prefix for resource names. Bucket names are globally unique across all of GCP, so this needs to be distinctive enough not to collide with a stranger's project."
  type        = string
}

variable "location" {
  description = "Bucket location — a region, dual-region, or multi-region."
  type        = string
}

variable "kms_key_id" {
  description = "Customer-managed key for objects in this bucket. The Cloud Storage service agent needs cryptoKeyEncrypterDecrypter on it, which modules/security grants."
  type        = string
  default     = null
}

variable "retention_days" {
  description = "Retention period in days. Null means no retention policy. Combined with lock_retention_policy, this is the WORM window."
  type        = number
  default     = null
}

variable "lock_retention_policy" {
  description = <<-EOT
    Lock the retention policy. **Irreversible.**

    Once locked, the retention period can only be increased, objects cannot be deleted
    before they age out, and the bucket cannot be deleted while any object is still under
    retention. No principal can undo this — not the project owner, not Google support.

    There is no default. A commitment of this shape should be stated, not inherited.
  EOT

  type = bool
}

variable "transition_nearline_days" {
  description = "Age at which objects move to NEARLINE. Null disables the transition."
  type        = number
  default     = null
}

variable "transition_coldline_days" {
  description = "Age at which objects move to COLDLINE. Null disables the transition."
  type        = number
  default     = null
}

variable "expiration_days" {
  description = "Age at which objects are deleted. Null keeps them indefinitely. Under a retention policy, deletion waits until the object is past retention regardless of this value."
  type        = number
  default     = null
}

variable "writer_members" {
  description = "Principals granted objectCreator, keyed by name. Append-only by design — objectAdmin would let a writer delete what it wrote."
  type        = map(string)
  default     = {}
}

variable "reader_members" {
  description = "Principals granted objectViewer, keyed by name."
  type        = map(string)
  default     = {}
}

variable "labels" {
  description = "Labels applied to the bucket."
  type        = map(string)
  default     = {}
}
