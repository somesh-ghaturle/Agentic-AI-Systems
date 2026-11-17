variable "project_id" {
  description = "GCP project that owns the state bucket."
  type        = string
}

variable "project" {
  description = "Project label. Use the same value the environment roots use."
  type        = string
  default     = "agentic"
}

variable "location" {
  description = "Bucket location. A multi-region such as US survives the loss of one region."
  type        = string
  default     = "US"
}

variable "state_versions_to_keep" {
  description = "How many superseded state generations stay recoverable."
  type        = number
  default     = 30

  validation {
    condition     = var.state_versions_to_keep >= 5
    error_message = "Keep at least 5 old state generations; fewer leaves no room to notice a bad apply."
  }
}
