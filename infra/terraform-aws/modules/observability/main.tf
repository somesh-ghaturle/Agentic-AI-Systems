# Observability — PRODUCTION-PRINCIPLES.md "Observability, security, and privacy"
#
# "This is the single highest-value investment in the system. It is what makes evaluation,
#  debugging, cost work, and incident response possible, and it is nearly impossible to
#  reconstruct after the fact."
#
# Terraform can create the destination, the retention, the metrics, and the alarms. It
# cannot make your application emit the fields. The trace schema the doc requires is
# documented in outputs.tf and HOW-TO-DEPLOY.md — emitting it is application work.

terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

resource "aws_cloudwatch_log_group" "traces" {
  name              = "/agentic/${var.name_prefix}/traces"
  retention_in_days = var.log_retention_days
  kms_key_id        = var.kms_key_arn

  tags = merge(var.tags, {
    Component = "trace-log"
    Layer     = "observability"
  })
}

# ---------------------------------------------------------------------------
# Metric filters — turn structured trace fields into metrics you can alarm on.
#
# These assume the application emits JSON traces carrying the fields the doc lists:
# correlation_id, step, model_version, prompt_version, tokens, cost_usd, latency_ms,
# outcome. Without those fields these filters match nothing.
# ---------------------------------------------------------------------------

resource "aws_cloudwatch_log_metric_filter" "cost_per_request" {
  name           = "${var.name_prefix}-cost-usd"
  log_group_name = aws_cloudwatch_log_group.traces.name

  # Only the terminal record carries total request cost; matching every step would
  # multiply-count it.
  pattern = "{ $.cost_usd = * && $.event_type = \"request_complete\" }"

  metric_transformation {
    name      = "RequestCostUsd"
    namespace = local.metric_namespace
    value     = "$.cost_usd"
    unit      = "None"
  }
}

resource "aws_cloudwatch_log_metric_filter" "tokens" {
  name           = "${var.name_prefix}-tokens"
  log_group_name = aws_cloudwatch_log_group.traces.name

  pattern = "{ $.total_tokens = * && $.event_type = \"request_complete\" }"

  metric_transformation {
    name      = "RequestTokens"
    namespace = local.metric_namespace
    value     = "$.total_tokens"
    unit      = "Count"
  }
}

resource "aws_cloudwatch_log_metric_filter" "schema_validation_failure" {
  name           = "${var.name_prefix}-schema-failures"
  log_group_name = aws_cloudwatch_log_group.traces.name

  # A structured-output contract violation. Rising counts here usually mean a model or
  # prompt version changed underneath you — BUILDING-BLOCKS.md §1.
  pattern = "{ $.event_type = \"schema_validation_failed\" }"

  metric_transformation {
    name      = "SchemaValidationFailures"
    namespace = local.metric_namespace
    value     = "1"
    unit      = "Count"
    # Explicit zero so the alarm evaluates instead of sitting in INSUFFICIENT_DATA when
    # nothing is failing.
    default_value = "0"
  }
}

resource "aws_cloudwatch_log_metric_filter" "loop_bound_hit" {
  name           = "${var.name_prefix}-loop-bound-hit"
  log_group_name = aws_cloudwatch_log_group.traces.name

  # The bounded-loop guard firing. Every occurrence is a workflow that could not finish
  # within its step budget — worth investigating, never worth ignoring.
  pattern = "{ $.event_type = \"loop_bound_exceeded\" }"

  metric_transformation {
    name          = "LoopBoundExceeded"
    namespace     = local.metric_namespace
    value         = "1"
    unit          = "Count"
    default_value = "0"
  }
}

locals {
  metric_namespace = "Agentic/${var.name_prefix}"
}

# ---------------------------------------------------------------------------
# Alarms — on the failure modes the architecture docs actually name.
# ---------------------------------------------------------------------------

resource "aws_cloudwatch_metric_alarm" "daily_cost" {
  count = var.daily_cost_threshold_usd == null ? 0 : 1

  alarm_name  = "${var.name_prefix}-daily-cost"
  namespace   = local.metric_namespace
  metric_name = "RequestCostUsd"
  statistic   = "Sum"
  period      = 86400

  comparison_operator = "GreaterThanThreshold"
  threshold           = var.daily_cost_threshold_usd
  evaluation_periods  = 1

  alarm_description  = "Daily spend exceeded threshold. Usual causes: an unbounded loop, a routing regression sending cheap steps to a frontier model, or unbounded context growth."
  alarm_actions      = var.alarm_topic_arns
  treat_missing_data = "notBreaching"

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "schema_failures" {
  count = var.schema_failure_threshold == null ? 0 : 1

  alarm_name  = "${var.name_prefix}-schema-failures"
  namespace   = local.metric_namespace
  metric_name = "SchemaValidationFailures"
  statistic   = "Sum"
  period      = 300

  comparison_operator = "GreaterThanThreshold"
  threshold           = var.schema_failure_threshold
  evaluation_periods  = 1

  alarm_description  = "Structured output contracts failing validation. Often means a model or prompt version changed."
  alarm_actions      = var.alarm_topic_arns
  treat_missing_data = "notBreaching"

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "loop_bound" {
  alarm_name  = "${var.name_prefix}-loop-bound-exceeded"
  namespace   = local.metric_namespace
  metric_name = "LoopBoundExceeded"
  statistic   = "Sum"
  period      = 300

  comparison_operator = "GreaterThanThreshold"
  threshold           = 0
  evaluation_periods  = 1

  alarm_description  = "An agent loop hit its step bound. Every occurrence is a workflow that could not complete within budget."
  alarm_actions      = var.alarm_topic_arns
  treat_missing_data = "notBreaching"

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "orchestrator_failures" {
  count = var.state_machine_arn == null ? 0 : 1

  alarm_name  = "${var.name_prefix}-orchestrator-failures"
  namespace   = "AWS/States"
  metric_name = "ExecutionsFailed"
  statistic   = "Sum"
  period      = 300

  dimensions = {
    StateMachineArn = var.state_machine_arn
  }

  comparison_operator = "GreaterThanThreshold"
  threshold           = var.execution_failure_threshold
  evaluation_periods  = 1

  alarm_description  = "Orchestrator executions failing."
  alarm_actions      = var.alarm_topic_arns
  treat_missing_data = "notBreaching"

  tags = var.tags
}

# A workflow blocked on a human is invisible in ordinary failure metrics — it is not
# failing, it is waiting. Long waits are their own failure mode, and gate fatigue starts
# here. BUILDING-BLOCKS.md §6.
resource "aws_cloudwatch_metric_alarm" "approvals_timing_out" {
  count = var.state_machine_arn == null ? 0 : 1

  alarm_name  = "${var.name_prefix}-approvals-timing-out"
  namespace   = "AWS/States"
  metric_name = "ExecutionsTimedOut"
  statistic   = "Sum"
  period      = 3600

  dimensions = {
    StateMachineArn = var.state_machine_arn
  }

  comparison_operator = "GreaterThanThreshold"
  threshold           = 0
  evaluation_periods  = 1

  alarm_description  = "Executions timing out — commonly approval requests nobody acted on. Check whether reviewers are receiving and reading them."
  alarm_actions      = var.alarm_topic_arns
  treat_missing_data = "notBreaching"

  tags = var.tags
}
