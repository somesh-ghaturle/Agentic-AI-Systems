variable "project_id" {
  description = "GCP project."
  type        = string
}

variable "name_prefix" {
  description = "Prefix for resource names. The source bucket name derives from this and must be globally unique."
  type        = string
}

variable "location" {
  description = "Region for the functions, source bucket, and Pub/Sub resources."
  type        = string
}

variable "firestore_location" {
  description = "Firestore location for the approvals database. Immutable after creation."
  type        = string
}

variable "approvals_collection" {
  description = "Collection holding approval records. Must match what the handlers read and write; nothing validates the agreement."
  type        = string
  default     = "approvals"
}

# --- identities ------------------------------------------------------------

variable "validator_service_account_email" {
  description = "Runtime service account email for the validator function."
  type        = string
}

variable "executor_service_account_email" {
  description = "Runtime service account email for the executor function."
  type        = string
}

variable "validator_member" {
  description = "Validator principal in `serviceAccount:...` form."
  type        = string
}

variable "executor_member" {
  description = "Executor principal in `serviceAccount:...` form. This is the member modules/tools grants run.invoker on write tools."
  type        = string
}

variable "orchestrator_member" {
  description = "Orchestrator principal. Granted invoke on the validator only — it opens approvals and never resolves them."
  type        = string
}

variable "approver_members" {
  description = "Principals permitted to resolve approvals, keyed by name. Empty means nobody can approve anything: safe, but every gated action will sit until its window closes."
  type        = map(string)
  default     = {}
}

# --- packages --------------------------------------------------------------

variable "validator_package_path" {
  description = "Local path to the validator deployment zip."
  type        = string
}

variable "executor_package_path" {
  description = "Local path to the executor deployment zip."
  type        = string
}

variable "runtime" {
  description = "Cloud Functions runtime for both handlers."
  type        = string
  default     = "python312"
}

variable "validator_entry_point" {
  description = "Exported function name the validator package registers."
  type        = string
  default     = "handler"
}

variable "executor_entry_point" {
  description = "Exported function name the executor package registers."
  type        = string
  default     = "handler"
}

# --- sizing ----------------------------------------------------------------

variable "validator_timeout_seconds" {
  description = "Validator timeout. It performs ownership and limit checks, not model calls, so this should be short."
  type        = number
  default     = 30
}

variable "validator_memory_mb" {
  description = "Validator memory."
  type        = number
  default     = 512
}

variable "validator_max_instances" {
  description = "Validator concurrency ceiling."
  type        = number
  default     = 10
}

variable "executor_timeout_seconds" {
  description = "Executor timeout. Must exceed the slowest write tool it invokes, or the write completes and the executor is killed before recording the outcome."
  type        = number
  default     = 120
}

variable "executor_memory_mb" {
  description = "Executor memory."
  type        = number
  default     = 512
}

variable "executor_max_instances" {
  description = "Executor concurrency ceiling. Low on purpose: every instance is a thing that can move money."
  type        = number
  default     = 3
}

variable "stale_claim_seconds" {
  description = "How long a claim may sit in `executing` before another executor may reclaim it. Safe only because write tools are idempotent on the approval ID."
  type        = number
  default     = 900
}

# --- durability ------------------------------------------------------------

variable "enable_point_in_time_recovery" {
  description = "PITR on the approvals database. Prod on — this is the record of who authorized what."
  type        = bool
  default     = false
}

variable "enable_delete_protection" {
  description = "Refuse API-level deletion of the approvals database."
  type        = bool
  default     = false
}

variable "message_retention_duration" {
  description = "Pub/Sub retention, as a duration string. Should not exceed the workflow's approval window: a request that outlives its own window is noise."
  type        = string
  default     = "86400s"
}

# --- wiring ----------------------------------------------------------------

variable "common_environment" {
  description = "Environment variables merged into both functions."
  type        = map(string)
  default     = {}
}

variable "validator_environment" {
  description = "Validator-specific environment variables."
  type        = map(string)
  default     = {}
}

variable "executor_environment" {
  description = "Executor-specific environment variables. This is where write tool URLs are supplied, and the executor is the only place they belong."
  type        = map(string)
  default     = {}
}

variable "trace_log_name" {
  description = "Shared trace log name, injected as TRACE_LOG_NAME."
  type        = string
  default     = null
}

variable "ingress_settings" {
  description = "Cloud Run ingress for both functions."
  type        = string
  default     = "ALLOW_ALL"
}

variable "kms_key_id" {
  description = "Customer-managed key for the topic and source bucket."
  type        = string
  default     = null
}

variable "labels" {
  description = "Labels applied to every resource in this module that supports them."
  type        = map(string)
  default     = {}
}
