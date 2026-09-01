variable "project_id" {
  description = "GCP project hosting the tool function."
  type        = string
}

variable "location" {
  description = "GCP region."
  type        = string
}

variable "name_prefix" {
  description = "Prefix for the function."
  type        = string
}

variable "source_bucket" {
  description = "Existing bucket containing the function source archive."
  type        = string
  default     = null
}

variable "source_object" {
  description = "Existing object containing the function source archive."
  type        = string
  default     = null
}

variable "enable_resources" {
  description = "Create cloud resources only when explicitly enabled."
  type        = bool
  default     = false
}
