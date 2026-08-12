# Orchestration control layer — BUILDING-BLOCKS.md section 4
#
# Step Functions implements the four non-negotiables the doc names directly:
#
#   Every loop is bounded      → max-steps guard in the state machine, plus a timeout
#   Every step is resumable    → execution state persists outside the process
#   Every step is traceable    → one correlation ID from request to response, X-Ray on
#   Failure paths are designed → explicit Catch/Retry per state, not discovered in prod
#
# The doc is also clear that plain application code is underrated: "If your flow is five
# known steps, five function calls with error handling beats a framework." Reach for this
# module when you have branching, retry loops, AND human-in-the-loop gates — the three
# things graph orchestration actually buys. With none of them, this is overhead.
#
# The state machine definition lives in the caller's hands (var.definition) because the
# flow is the application. What this module owns is the surrounding guarantees.

terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

resource "aws_sfn_state_machine" "orchestrator" {
  name     = "${var.name_prefix}-orchestrator"
  role_arn = aws_iam_role.orchestrator.arn
  type     = var.state_machine_type

  definition = var.definition

  # Full execution history. This is the trace the archive keeps and the eval set is built
  # from — PRODUCTION-PRINCIPLES.md calls it "the single highest-value investment."
  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.orchestrator.arn}:*"
    include_execution_data = var.log_execution_data
    level                  = "ALL"
  }

  tracing_configuration {
    enabled = true
  }

  tags = merge(var.tags, {
    Component = "orchestrator"
    Layer     = "orchestration"
  })

  # An EXPRESS machine cannot hold a task token, so an approval gate configured against
  # one silently is not a gate. Fail at plan time instead of discovering it in review.
  lifecycle {
    precondition {
      condition     = var.approval_topic_arn == null || var.state_machine_type == "STANDARD"
      error_message = "Approval gates require state_machine_type = \"STANDARD\": EXPRESS does not support waitForTaskToken, so the human-in-the-loop step would not block."
    }
  }
}

resource "aws_cloudwatch_log_group" "orchestrator" {
  name              = "/aws/states/${var.name_prefix}-orchestrator"
  retention_in_days = var.log_retention_days
  kms_key_id        = var.kms_key_arn

  tags = var.tags
}

# ---------------------------------------------------------------------------
# Execution role — least privilege, per PRODUCTION-PRINCIPLES.md
#
# "Each tool gets exactly the access it needs." The orchestrator invokes tools and
# reads/writes execution state. It does NOT get blanket lambda:InvokeFunction on the
# account, which is the common shortcut and the one that turns a confused agent into a
# lateral-movement problem.
# ---------------------------------------------------------------------------

resource "aws_iam_role" "orchestrator" {
  name = "${var.name_prefix}-orchestrator"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "states.amazonaws.com" }
      Action    = "sts:AssumeRole"
      Condition = {
        StringEquals = { "aws:SourceAccount" = data.aws_caller_identity.current.account_id }
      }
    }]
  })

  tags = var.tags
}

data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "orchestrator" {
  # Tool invocation, scoped to the tool functions this system actually has.
  dynamic "statement" {
    for_each = length(var.tool_function_arns) > 0 ? [1] : []
    content {
      sid       = "InvokeToolFunctions"
      effect    = "Allow"
      actions   = ["lambda:InvokeFunction"]
      resources = var.tool_function_arns
    }
  }

  # Execution state: read and write on every step.
  dynamic "statement" {
    for_each = var.state_table_arn == null ? [] : [1]
    content {
      sid    = "ExecutionState"
      effect = "Allow"
      actions = [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query",
      ]
      resources = [var.state_table_arn]
    }
  }

  # Trace archive: write-once. Deliberately no s3:DeleteObject — the orchestrator must
  # not be able to destroy its own audit trail.
  dynamic "statement" {
    for_each = var.archive_bucket_arn == null ? [] : [1]
    content {
      sid       = "WriteTraceArchive"
      effect    = "Allow"
      actions   = ["s3:PutObject"]
      resources = ["${var.archive_bucket_arn}/*"]
    }
  }

  # Human approval gate: publish the proposal for a person to review.
  dynamic "statement" {
    for_each = var.approval_topic_arn == null ? [] : [1]
    content {
      sid       = "PublishApprovalRequest"
      effect    = "Allow"
      actions   = ["sns:Publish"]
      resources = [var.approval_topic_arn]
    }
  }

  statement {
    sid    = "Observability"
    effect = "Allow"
    actions = [
      "logs:CreateLogDelivery",
      "logs:GetLogDelivery",
      "logs:UpdateLogDelivery",
      "logs:DeleteLogDelivery",
      "logs:ListLogDeliveries",
      "logs:PutResourcePolicy",
      "logs:DescribeResourcePolicies",
      "logs:DescribeLogGroups",
      "xray:PutTraceSegments",
      "xray:PutTelemetryRecords",
      "xray:GetSamplingRules",
      "xray:GetSamplingTargets",
    ]
    # These Step Functions logging and X-Ray actions do not support resource-level
    # permissions; AWS requires "*". Noted so it does not read as an oversight.
    resources = ["*"]
  }

  dynamic "statement" {
    for_each = var.kms_key_arn == null ? [] : [1]
    content {
      sid       = "UseKmsKey"
      effect    = "Allow"
      actions   = ["kms:Decrypt", "kms:GenerateDataKey"]
      resources = [var.kms_key_arn]
    }
  }
}

resource "aws_iam_role_policy" "orchestrator" {
  name   = "${var.name_prefix}-orchestrator"
  role   = aws_iam_role.orchestrator.id
  policy = data.aws_iam_policy_document.orchestrator.json
}
