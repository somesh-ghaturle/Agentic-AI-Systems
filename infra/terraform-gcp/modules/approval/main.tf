# The approval gate.
#
# Two functions, one topic, one database. The validator decides whether a proposal is
# worth a human's attention; the executor is the only thing in the system that may invoke
# a write tool.
#
# The ordering matters and is easy to get backwards: validation happens *before*
# notification. Invalid proposals never reach a person. From
# terraform-aws/ARCHITECTURE.md section 3:
#
#   "This is what keeps approval requests meaningful — a reviewer who sees mostly junk
#    stops reading, and gate fatigue is how a gate fails while appearing to work."

terraform {
  required_version = ">= 1.6"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.44"
    }
  }
}

locals {
  validator_name = "${var.name_prefix}-approval-validator"
  executor_name  = "${var.name_prefix}-approval-executor"
}

# ---------------------------------------------------------------------------
# Approval records
#
# Separate from the execution-state database. These are the record of who authorized
# what, and they outlive the execution that produced them.
# ---------------------------------------------------------------------------

resource "google_firestore_database" "approvals" {
  project = var.project_id

  name        = "${var.name_prefix}-approvals"
  location_id = var.firestore_location

  type = "FIRESTORE_NATIVE"

  # Pessimistic, unlike the execution-state database. The executor's claim is a
  # read-then-conditional-write, and two executors racing on a redelivered Pub/Sub message
  # is the exact scenario this database exists to survive. Optimistic mode resolves that
  # race by retrying, which is correct but noisier under contention.
  concurrency_mode = "PESSIMISTIC"

  point_in_time_recovery_enablement = var.enable_point_in_time_recovery ? "POINT_IN_TIME_RECOVERY_ENABLED" : "POINT_IN_TIME_RECOVERY_DISABLED"

  delete_protection_state = var.enable_delete_protection ? "DELETE_PROTECTION_ENABLED" : "DELETE_PROTECTION_DISABLED"
  deletion_policy         = var.enable_delete_protection ? "ABANDON" : "DELETE"
}

# The stale-claim reaper scans for records stuck in `executing` past their claim age. That
# query is an equality filter on status plus an ordering on claim time, which Firestore
# will not serve without this index.
resource "google_firestore_index" "approvals_by_status" {
  project    = var.project_id
  database   = google_firestore_database.approvals.name
  collection = var.approvals_collection

  fields {
    field_path = "status"
    order      = "ASCENDING"
  }

  fields {
    field_path = "claimed_at"
    order      = "ASCENDING"
  }
}

# ---------------------------------------------------------------------------
# Notification
# ---------------------------------------------------------------------------

resource "google_pubsub_topic" "approval_requests" {
  project = var.project_id
  name    = "${var.name_prefix}-approval-requests"

  kms_key_name = var.kms_key_id

  # Long enough that a subscriber outage does not lose an approval request, short enough
  # that a request nobody consumed is not still sitting there next week looking actionable.
  message_retention_duration = var.message_retention_duration

  labels = var.labels
}

resource "google_pubsub_subscription" "approvers" {
  project = var.project_id
  name    = "${var.name_prefix}-approval-requests-sub"
  topic   = google_pubsub_topic.approval_requests.id

  # An approval request that outlives its own approval window is noise. This should be no
  # longer than the workflow's approval timeout.
  message_retention_duration = var.message_retention_duration
  expiration_policy {
    ttl = "" # never expire the subscription itself
  }

  ack_deadline_seconds = 60

  labels = var.labels
}

# Only the validator publishes approval requests. Notably the orchestrator does not: it
# can ask for validation, but it cannot put a request in front of a human directly, which
# would let it route around the validator's ownership and limit checks.
resource "google_pubsub_topic_iam_member" "publisher" {
  project = var.project_id
  topic   = google_pubsub_topic.approval_requests.name
  role    = "roles/pubsub.publisher"
  member  = var.validator_member
}

resource "google_pubsub_subscription_iam_member" "subscriber" {
  for_each = var.approver_members

  project      = var.project_id
  subscription = google_pubsub_subscription.approvers.name
  role         = "roles/pubsub.subscriber"
  member       = each.value
}

# ---------------------------------------------------------------------------
# Source packages
# ---------------------------------------------------------------------------

resource "google_storage_bucket" "source" {
  project = var.project_id

  name     = "${var.name_prefix}-approval-source"
  location = var.location

  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  dynamic "encryption" {
    for_each = var.kms_key_id == null ? [] : [var.kms_key_id]
    content {
      default_kms_key_name = encryption.value
    }
  }

  labels = var.labels
}

resource "google_storage_bucket_object" "validator" {
  name   = "validator/${filemd5(var.validator_package_path)}.zip"
  bucket = google_storage_bucket.source.name
  source = var.validator_package_path
}

resource "google_storage_bucket_object" "executor" {
  name   = "executor/${filemd5(var.executor_package_path)}.zip"
  bucket = google_storage_bucket.source.name
  source = var.executor_package_path
}

# ---------------------------------------------------------------------------
# The validator
# ---------------------------------------------------------------------------

resource "google_cloudfunctions2_function" "validator" {
  project  = var.project_id
  location = var.location

  name        = local.validator_name
  description = "Validates write proposals — ownership, permission, limits — before any human is notified."

  build_config {
    runtime     = var.runtime
    entry_point = var.validator_entry_point

    source {
      storage_source {
        bucket = google_storage_bucket.source.name
        object = google_storage_bucket_object.validator.name
      }
    }
  }

  service_config {
    timeout_seconds       = var.validator_timeout_seconds
    available_memory      = "${var.validator_memory_mb}M"
    max_instance_count    = var.validator_max_instances
    service_account_email = var.validator_service_account_email

    environment_variables = merge(
      var.common_environment,
      var.validator_environment,
      {
        APPROVALS_DATABASE   = google_firestore_database.approvals.name
        APPROVALS_COLLECTION = var.approvals_collection
        APPROVAL_TOPIC       = google_pubsub_topic.approval_requests.id
      },
      var.trace_log_name == null ? {} : { TRACE_LOG_NAME = var.trace_log_name },
    )

    ingress_settings               = var.ingress_settings
    all_traffic_on_latest_revision = true
  }

  labels = merge(var.labels, { component = "approval-validator", layer = "approval" })
}

# The orchestrator asks for validation. That is the whole of its involvement in the write
# path.
resource "google_cloud_run_service_iam_member" "validator_from_orchestrator" {
  project  = var.project_id
  location = var.location
  service  = google_cloudfunctions2_function.validator.name

  role   = "roles/run.invoker"
  member = var.orchestrator_member
}

# ---------------------------------------------------------------------------
# The executor
#
# The only principal permitted to invoke a write tool. modules/tools grants it
# run.invoker on each write tool and grants that role to nothing else.
# ---------------------------------------------------------------------------

resource "google_cloudfunctions2_function" "executor" {
  project  = var.project_id
  location = var.location

  name        = local.executor_name
  description = "Resolves an approval and invokes the write tool. The only principal with run.invoker on write tools."

  build_config {
    runtime     = var.runtime
    entry_point = var.executor_entry_point

    source {
      storage_source {
        bucket = google_storage_bucket.source.name
        object = google_storage_bucket_object.executor.name
      }
    }
  }

  service_config {
    timeout_seconds       = var.executor_timeout_seconds
    available_memory      = "${var.executor_memory_mb}M"
    service_account_email = var.executor_service_account_email

    # Deliberately low. Every instance of this function is a thing that can move money,
    # and a redelivered notification storm should queue rather than fan out.
    max_instance_count = var.executor_max_instances

    environment_variables = merge(
      var.common_environment,
      var.executor_environment,
      {
        APPROVALS_DATABASE   = google_firestore_database.approvals.name
        APPROVALS_COLLECTION = var.approvals_collection

        # How long a claim may sit in `executing` before another executor may reclaim it.
        # Safe only because write tools are idempotent on the approval ID — see
        # ARCHITECTURE.md section 4.
        STALE_CLAIM_SECONDS = tostring(var.stale_claim_seconds)
      },
      var.trace_log_name == null ? {} : { TRACE_LOG_NAME = var.trace_log_name },
    )

    ingress_settings               = var.ingress_settings
    all_traffic_on_latest_revision = true
  }

  labels = merge(var.labels, { component = "approval-executor", layer = "approval" })
}

# Approvers resolve approvals. Nobody else can reach the executor — notably not the
# orchestrator, which would otherwise be able to approve its own proposals.
#
# An empty set means nobody can approve anything. That is safe, and it is also a system
# where every gated action sits until its window closes, so it is worth noticing rather
# than discovering.
resource "google_cloud_run_service_iam_member" "executor_from_approver" {
  for_each = var.approver_members

  project  = var.project_id
  location = var.location
  service  = google_cloudfunctions2_function.executor.name

  role   = "roles/run.invoker"
  member = each.value
}

# ---------------------------------------------------------------------------
# Data-plane grants
# ---------------------------------------------------------------------------

resource "google_project_iam_member" "firestore_access" {
  for_each = toset(compact([var.validator_member, var.executor_member]))

  project = var.project_id
  role    = "roles/datastore.user"
  member  = each.value
}

# The executor resolves the workflow's callback, which resumes the suspended execution.
# Without this the write happens and the orchestrator waits out its timeout anyway, which
# reads as an approval nobody answered.
resource "google_project_iam_member" "executor_workflow_callback" {
  project = var.project_id
  role    = "roles/workflows.invoker"
  member  = var.executor_member
}
