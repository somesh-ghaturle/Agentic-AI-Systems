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

variable "allowed_ip_list" {
  description = "CIDRs permitted to authenticate as the service users. No default: an accidentally empty allow-list creates no network policy at all, which fails open, and prod is the one environment where that must be impossible to do by omission."
  type        = list(string)

  validation {
    condition     = length(var.allowed_ip_list) > 0
    error_message = "allowed_ip_list must be non-empty in prod. An empty list creates no policy and leaves the service users reachable from anywhere."
  }
}

variable "warehouse_size" {
  description = "Warehouse size. Larger than dev only if measurement says so — agent workloads are many small queries, and a bigger warehouse makes each cost more without finishing sooner."
  type        = string
  default     = "SMALL"
}

variable "approver_roles" {
  description = "Human roles permitted to call APPROVE, keyed by name. No default in prod: a production approval gate with no approver is a gate that can never open, and discovering that from a backlog of PENDING proposals is a worse way to learn it than an apply-time error."
  type        = map(string)

  validation {
    condition     = length(var.approver_roles) > 0
    error_message = "approver_roles must name at least one human role in prod. With none, every proposal stays PENDING forever."
  }
}

variable "cost_monitor_credit_quota" {
  description = "Monthly credit quota for the warehouse's resource monitor. Null (the default) leaves prod unmonitored until an operator sets this from observed spend plus headroom — the same reasoning modules/state's own variable gives for not guessing a number here. Suspension is left off in this environment's wiring regardless of quota; see modules/state/variables.tf on why."
  type        = number
  default     = null
}
