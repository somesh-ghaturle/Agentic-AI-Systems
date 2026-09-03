variable "name_prefix" {
  description = "Prefix for the state machine."
  type        = string
}

# The definition stays opaque to this module. The cross-cloud endpoints are
# resolved by the caller, which is the only layer that can see both the GCP and
# Azure modules; embedding them here would require decoding and re-encoding a
# state machine this module does not own.
variable "definition" {
  description = "Step Functions definition supplied by the application."
  type        = string
}

variable "enable_resources" {
  description = "Create cloud resources only when explicitly enabled."
  type        = bool
  default     = false
}
