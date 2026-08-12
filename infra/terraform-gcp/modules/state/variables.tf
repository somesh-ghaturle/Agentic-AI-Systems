variable "project_id" {
  description = "GCP project."
  type        = string
}

variable "name_prefix" {
  description = "Prefix for resource names, typically \"<project>-<env>\"."
  type        = string
}

variable "location" {
  description = "Firestore location — a region like `us-central1` or a multi-region like `nam5`. Immutable after creation."
  type        = string
}

variable "executions_collection" {
  description = "Collection holding one document per execution. Must match what the handlers write to; nothing validates the agreement."
  type        = string
  default     = "executions"
}

variable "enable_point_in_time_recovery" {
  description = "Retain a rolling recovery window. Prod on, dev off."
  type        = bool
  default     = false
}

variable "enable_delete_protection" {
  description = "Refuse API-level deletion of the database, and make Terraform abandon rather than destroy it. Prod on."
  type        = bool
  default     = false
}

variable "datastore_user_members" {
  description = "Principals granted roles/datastore.user, keyed by name. Note this role is project-wide and covers every Firestore database in the project — see the comment in main.tf."
  type        = map(string)
  default     = {}
}
