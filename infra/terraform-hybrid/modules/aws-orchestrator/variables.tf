variable "name_prefix" {
  description = "Prefix for the state machine."
  type        = string
}

variable "definition" {
  description = "Step Functions definition supplied by the application."
  type        = string
}

variable "tool_endpoint" {
  description = "GCP tool endpoint passed to the state machine."
  type        = string
  default     = null
}

variable "state_endpoint" {
  description = "Azure state endpoint passed to the state machine."
  type        = string
  default     = null
}

variable "enable_resources" {
  description = "Create cloud resources only when explicitly enabled."
  type        = bool
  default     = false
}
