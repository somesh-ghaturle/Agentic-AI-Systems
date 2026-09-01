variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "gcp_project_id" {
  type        = string
  description = "Set locally; no project is committed to this repository."
  default     = "replace-me"
}

variable "gcp_region" {
  type    = string
  default = "us-central1"
}

variable "azure_resource_group_name" {
  type    = string
  default = "replace-me"
}

variable "azure_location" {
  type    = string
  default = "eastus"
}

variable "enable_resources" {
  description = "Opt in only after reviewing all providers and costs."
  type        = bool
  default     = false
}
