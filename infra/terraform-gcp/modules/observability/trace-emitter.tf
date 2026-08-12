# The trace emitter.
#
# A workflow cannot write to the shared trace log. `sys.log` inside a Workflows definition
# writes to that workflow's own execution log, under the Workflows resource type — not to
# `projects/<project>/logs/<trace log name>` where every metric in main.tf is filtering.
#
# So the orchestrator's own records — the terminal outcome, the loop bound firing, the
# cost total — reach the metrics only by calling this function. From
# terraform-aws/ARCHITECTURE.md section 5:
#
#   "Omit that function and the loop-bound and cost alarms sit at zero forever, which
#    reads exactly like a healthy system."
#
# That sentence is the reason this exists as infrastructure rather than as a note telling
# handler authors to remember something.

resource "google_storage_bucket" "trace_emitter_source" {
  count = var.trace_emitter == null ? 0 : 1

  project = var.project_id

  name     = "${var.name_prefix}-emitter-source"
  location = var.location

  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  labels = var.labels
}

resource "google_storage_bucket_object" "trace_emitter" {
  count = var.trace_emitter == null ? 0 : 1

  name   = "emitter/${filemd5(var.trace_emitter.package_path)}.zip"
  bucket = google_storage_bucket.trace_emitter_source[0].name
  source = var.trace_emitter.package_path
}

resource "google_cloudfunctions2_function" "trace_emitter" {
  count = var.trace_emitter == null ? 0 : 1

  project  = var.project_id
  location = var.location

  name        = "${var.name_prefix}-trace-emitter"
  description = "Writes orchestrator records to the shared trace log, where the log-based metrics can see them."

  build_config {
    runtime     = var.trace_emitter.runtime
    entry_point = var.trace_emitter.entry_point

    source {
      storage_source {
        bucket = google_storage_bucket.trace_emitter_source[0].name
        object = google_storage_bucket_object.trace_emitter[0].name
      }
    }
  }

  service_config {
    timeout_seconds       = 30
    available_memory      = "256M"
    max_instance_count    = 20
    service_account_email = var.trace_emitter.service_account_email

    environment_variables = {
      TRACE_LOG_NAME = local.trace_log_name
      GCP_PROJECT    = var.project_id
    }

    ingress_settings               = var.ingress_settings
    all_traffic_on_latest_revision = true
  }

  labels = merge(var.labels, { component = "trace-emitter", layer = "observability" })
}

# Only the orchestrator calls this. It is not a general-purpose logging endpoint, and
# opening it wider would let any principal write entries that the cost and loop-bound
# alerts treat as authoritative.
resource "google_cloud_run_service_iam_member" "trace_emitter_from_orchestrator" {
  count = var.trace_emitter == null ? 0 : 1

  project  = var.project_id
  location = var.location
  service  = google_cloudfunctions2_function.trace_emitter[0].name

  role   = "roles/run.invoker"
  member = var.trace_emitter.orchestrator_member
}

# Writing to a log the metrics watch requires logWriter. Without it the function returns
# 200, the workflow proceeds, and nothing is recorded — the failure is invisible from both
# ends.
resource "google_project_iam_member" "trace_emitter_log_writer" {
  count = var.trace_emitter == null ? 0 : 1

  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = var.trace_emitter.member
}

# Every other workload writes traces directly. Same grant, same reason.
resource "google_project_iam_member" "trace_writer" {
  for_each = var.trace_writer_members

  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = each.value
}
