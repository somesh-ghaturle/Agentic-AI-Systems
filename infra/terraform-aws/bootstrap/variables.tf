variable "project" {
  description = "Project name. Use the same value the environment roots use, so the bucket is recognisably theirs."
  type        = string
  default     = "agentic"
}

variable "region" {
  description = "Region the state bucket lives in. It does not have to match the environments' region."
  type        = string
  default     = "us-east-1"
}

variable "noncurrent_version_retention_days" {
  description = "Days a superseded state version stays recoverable before it is deleted."
  type        = number
  default     = 90

  validation {
    condition     = var.noncurrent_version_retention_days >= 7
    error_message = "Keep at least 7 days of old state versions; fewer leaves no time to notice a bad apply."
  }
}
