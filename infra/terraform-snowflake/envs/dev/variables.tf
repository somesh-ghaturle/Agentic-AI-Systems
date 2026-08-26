variable "organization_name" {
  description = "Snowflake organization name."
  type        = string
}

variable "account_name" {
  description = "Snowflake account name within the organization."
  type        = string
}

variable "workload_identity_provider" {
  description = "Which federated identity Terraform itself presents: AWS, AZURE, GCP or OIDC. Snowflake runs on one of the three clouds and this names which one this account sits on."
  type        = string
  default     = "AWS"

  validation {
    condition     = contains(["AWS", "AZURE", "GCP", "OIDC"], var.workload_identity_provider)
    error_message = "workload_identity_provider must be one of AWS, AZURE, GCP, OIDC."
  }
}

variable "terraform_role" {
  description = "Role Terraform runs as. Needs CREATE DATABASE and CREATE ROLE at the account level; deliberately not ACCOUNTADMIN."
  type        = string
  default     = "SYSADMIN"
}

variable "orchestrator_workload_arn" {
  description = "ARN of the workload identity permitted to become the orchestrator service user. No secret — an identity, matched at authentication time."
  type        = string
}

variable "executor_workload_arn" {
  description = "ARN of the workload identity permitted to become the executor service user."
  type        = string
}

variable "model_name" {
  description = "Cortex model backing the guarded entry point."
  type        = string
  default     = "claude-sonnet-4-5"
}

variable "approver_roles" {
  description = "Human roles permitted to call APPROVE, keyed by name. Empty fails closed: proposals accumulate as PENDING and nothing can claim them."
  type        = map(string)
  default     = {}
}
