variable "project_id" {
  description = "GCP project hosting the vector index."
  type        = string
}

variable "region" {
  description = "GCP region."
  type        = string
}

variable "name_prefix" {
  description = "Index display-name prefix."
  type        = string
}

variable "dimensions" {
  description = "Embedding dimensions expected by the index."
  type        = number
  default     = 384
}

variable "enable_resources" {
  description = "Create cloud resources only when explicitly enabled."
  type        = bool
  default     = false
}
