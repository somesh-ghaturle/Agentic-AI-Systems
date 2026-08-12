# Observability.
#
# Log-based metrics attach to **one** log name, not to each function's default log. From
# terraform-aws/ARCHITECTURE.md section 5:
#
#   "A handler that only prints to stdout looks healthy in the console and is invisible to
#    every alarm."
#
# On GCP the trap is sharper than on AWS, because anything a Cloud Functions handler
# writes to stdout is captured automatically and appears in Cloud Logging looking
# perfectly healthy. It lands in the function's own `cloudfunctions.googleapis.com/
# cloud-functions` log with no structured payload, so every filter below misses it and
# every alert sits at zero. The logs are right there in the console, which is what makes
# it convincing.
#
# Handlers must write structured entries to `TRACE_LOG_NAME` through the Cloud Logging
# API. That is a code property, not an infrastructure one, and it is listed as such in
# ARCHITECTURE.md section 7.

terraform {
  required_version = ">= 1.6"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

locals {
  trace_log_name = "${var.name_prefix}-traces"

  # Every metric below filters on this. Written once because a typo in one copy produces a
  # metric that is silently always zero.
  trace_filter = "logName=\"projects/${var.project_id}/logs/${local.trace_log_name}\""
}

# ---------------------------------------------------------------------------
# Log-based metrics
#
# Four, matching the AWS tree: schema failures, loop bounds, abandoned approvals, and cost.
# ---------------------------------------------------------------------------

resource "google_logging_metric" "schema_validation_failed" {
  project = var.project_id

  name        = "${var.name_prefix}-schema-validation-failed"
  description = "Structured output from the model failed schema validation."

  filter = "${local.trace_filter} AND jsonPayload.event=\"schema_validation_failed\""

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    unit        = "1"
  }
}

resource "google_logging_metric" "loop_bound_exceeded" {
  project = var.project_id

  name        = "${var.name_prefix}-loop-bound-exceeded"
  description = "An execution hit its step ceiling. An agent that loops is an agent spending money."

  filter = "${local.trace_filter} AND jsonPayload.event=\"loop_bound_exceeded\""

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    unit        = "1"
  }
}

resource "google_logging_metric" "approval_abandoned" {
  project = var.project_id

  name        = "${var.name_prefix}-approval-abandoned"
  description = "An approval window closed with nobody answering. This is the gate-fatigue signal."

  filter = "${local.trace_filter} AND jsonPayload.event=\"approval_abandoned\""

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    unit        = "1"
  }
}

# Cost belongs on the terminal record only. Emitting it per step multiply-counts spend,
# and this metric cannot tell the difference — it sums whatever it is given.
resource "google_logging_metric" "cost_usd" {
  project = var.project_id

  name        = "${var.name_prefix}-cost-usd"
  description = "Model spend, extracted from terminal execution records."

  filter = "${local.trace_filter} AND jsonPayload.terminal=true AND jsonPayload.cost_usd>0"

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "DISTRIBUTION"
    unit        = "1"
  }

  value_extractor = "EXTRACT(jsonPayload.cost_usd)"

  bucket_options {
    exponential_buckets {
      num_finite_buckets = 32
      growth_factor      = 2
      scale              = 0.001
    }
  }
}

# ---------------------------------------------------------------------------
# Notification and alerts
# ---------------------------------------------------------------------------

resource "google_monitoring_notification_channel" "email" {
  for_each = var.alert_email_receivers

  project = var.project_id

  display_name = "${var.name_prefix} ${each.key}"
  type         = "email"

  labels = {
    email_address = each.value
  }
}

locals {
  notification_channels = [for c in google_monitoring_notification_channel.email : c.id]

  # Each alert is the same shape: count a log-based metric over a window and fire above a
  # threshold. Expressed as data so the four policies do not drift apart.
  alerts = {
    schema-failures = {
      metric      = google_logging_metric.schema_validation_failed.name
      threshold   = var.schema_failure_threshold
      duration    = "300s"
      alignment   = "300s"
      description = "The model is returning output the schema rejects. Usually a prompt or tool-definition change; occasionally a model version change nobody announced."
    }
    runaway-loops = {
      metric      = google_logging_metric.loop_bound_exceeded.name
      threshold   = 0
      duration    = "0s"
      alignment   = "300s"
      description = "An execution hit its step ceiling. Threshold is zero because one occurrence is worth reading."
    }
    gate-fatigue = {
      metric      = google_logging_metric.approval_abandoned.name
      threshold   = var.abandoned_approval_threshold
      duration    = "0s"
      alignment   = "3600s"
      description = "Approvals are timing out unanswered. The gate still works and is no longer being used, which looks identical to a quiet system from every other angle."
    }
  }
}

resource "google_monitoring_alert_policy" "counted" {
  for_each = local.alerts

  project = var.project_id

  display_name = "${var.name_prefix} ${each.key}"
  combiner     = "OR"

  documentation {
    content   = each.value.description
    mime_type = "text/markdown"
  }

  conditions {
    display_name = each.key

    condition_threshold {
      filter = "resource.type=\"cloud_function\" AND metric.type=\"logging.googleapis.com/user/${each.value.metric}\""

      comparison      = "COMPARISON_GT"
      threshold_value = each.value.threshold
      duration        = each.value.duration

      aggregations {
        alignment_period   = each.value.alignment
        per_series_aligner = "ALIGN_DELTA"
      }
    }
  }

  notification_channels = local.notification_channels

  # Without this an alert that fires once stays open forever, and an operator who sees a
  # permanently red dashboard stops looking at it.
  alert_strategy {
    auto_close = "1800s"
  }
}

resource "google_monitoring_alert_policy" "daily_spend" {
  project = var.project_id

  display_name = "${var.name_prefix} daily-spend"
  combiner     = "OR"

  documentation {
    content   = "Model spend over the last day exceeded the threshold. In dev this is a runaway-loop detector rather than a budget."
    mime_type = "text/markdown"
  }

  conditions {
    display_name = "daily-spend"

    condition_threshold {
      filter = "resource.type=\"cloud_function\" AND metric.type=\"logging.googleapis.com/user/${google_logging_metric.cost_usd.name}\""

      comparison      = "COMPARISON_GT"
      threshold_value = var.daily_cost_threshold_usd
      duration        = "0s"

      aggregations {
        alignment_period   = "86400s"
        per_series_aligner = "ALIGN_SUM"
      }
    }
  }

  notification_channels = local.notification_channels

  alert_strategy {
    auto_close = "86400s"
  }
}

# The orchestrator's own failures. A workflow that fails does not write to the trace log —
# it writes to its own execution log — so this one filters on the Workflows resource
# rather than on the shared trace name.
resource "google_monitoring_alert_policy" "workflow_failures" {
  count = var.workflow_name == null ? 0 : 1

  project = var.project_id

  display_name = "${var.name_prefix} workflow-failures"
  combiner     = "OR"

  documentation {
    content   = "The orchestrator workflow is failing executions. Distinct from the trace-log alerts: a workflow that cannot start never emits a trace at all."
    mime_type = "text/markdown"
  }

  conditions {
    display_name = "workflow-failures"

    condition_threshold {
      filter = join(" AND ", [
        "resource.type=\"workflows.googleapis.com/Workflow\"",
        "resource.labels.workflow_id=\"${var.workflow_name}\"",
        "metric.type=\"workflows.googleapis.com/finished_execution_count\"",
        "metric.labels.status=\"FAILED\"",
      ])

      comparison      = "COMPARISON_GT"
      threshold_value = var.workflow_failure_threshold
      duration        = "0s"

      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_DELTA"
      }
    }
  }

  notification_channels = local.notification_channels

  alert_strategy {
    auto_close = "1800s"
  }
}

# ---------------------------------------------------------------------------
# Archival
#
# Traces route to the archive bucket. The sink's writer identity needs objectCreator on
# that bucket, and the caller wires it — see the output at the bottom of this file.
# ---------------------------------------------------------------------------

resource "google_logging_project_sink" "archive" {
  count = var.archive_bucket_name == null ? 0 : 1

  project = var.project_id
  name    = "${var.name_prefix}-trace-archive"

  destination = "storage.googleapis.com/${var.archive_bucket_name}"
  filter      = local.trace_filter

  # A dedicated service account for this sink rather than the shared Cloud Logging one.
  # With the shared identity, granting the sink write access to the archive grants every
  # sink in the project the same access.
  unique_writer_identity = true
}
