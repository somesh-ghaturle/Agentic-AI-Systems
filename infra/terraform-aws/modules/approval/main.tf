# Approval gates — BUILDING-BLOCKS.md §6
#
# The enforcement flow, and the components that own each step:
#
#   Model proposes action + arguments   → orchestrator
#   App code validates ownership/limits → validator Lambda (here)
#   Human approves                      → SNS notification + callback (here)
#   Tool executes                       → executor Lambda (here, the only caller of writes)
#   Log the full record                 → approval audit table (here)
#
# "The model proposes. Application code decides. A human authorizes. The tool executes.
#  Each of those is a distinct step owned by a distinct component. Collapsing any two of
#  them is how systems take actions nobody intended."
#
# The task-token pattern is what makes the human step real: the state machine blocks until
# someone calls SendTaskSuccess or SendTaskFailure. No token, no execution.

terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

data "aws_caller_identity" "current" {}

# ---------------------------------------------------------------------------
# Audit record — "Log the full record: proposal, validation result, who approved,
# when, and the outcome. That log is your audit trail and your incident evidence."
# ---------------------------------------------------------------------------

resource "aws_dynamodb_table" "approvals" {
  name         = "${var.name_prefix}-approvals"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "approval_id"
  range_key    = "created_at"

  attribute {
    name = "approval_id"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "S"
  }

  attribute {
    name = "correlation_id"
    type = "S"
  }

  # Answers "what did this request try to do?" during an incident, without a scan.
  global_secondary_index {
    name            = "by-correlation-id"
    hash_key        = "correlation_id"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  # Deliberately no TTL. Execution state expires; the approval record is evidence and
  # outlives the workflow that produced it.

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = var.kms_key_arn
  }

  tags = merge(var.tags, {
    Component = "approval-audit"
    Layer     = "approval-gate"
  })
}

# ---------------------------------------------------------------------------
# Notification path
# ---------------------------------------------------------------------------

resource "aws_sns_topic" "approval_requests" {
  name              = "${var.name_prefix}-approval-requests"
  kms_master_key_id = var.kms_key_arn

  tags = merge(var.tags, {
    Component = "approval-requests"
    Layer     = "approval-gate"
  })
}

# An approval that never reaches a human blocks the workflow until timeout. Failures to
# deliver need to be visible, not silent.
resource "aws_sns_topic" "approval_delivery_failures" {
  name              = "${var.name_prefix}-approval-delivery-failures"
  kms_master_key_id = var.kms_key_arn

  tags = var.tags
}

# ---------------------------------------------------------------------------
# Validator — application code, deterministic, runs BEFORE the human sees anything
#
# "Only refund orders belonging to the requesting user" is a rule the model will follow
# almost always. Almost always is not an authorization model.
#
# Rejecting invalid proposals here also protects the human from gate fatigue: they only
# see proposals that already passed ownership, permission, and limit checks.
# ---------------------------------------------------------------------------

resource "aws_lambda_function" "validator" {
  function_name = "${var.name_prefix}-approval-validator"
  role          = aws_iam_role.validator.arn
  handler       = var.validator.handler
  runtime       = var.validator.runtime
  filename      = var.validator.package_path

  source_code_hash = filebase64sha256(var.validator.package_path)

  timeout     = var.validator.timeout_seconds
  memory_size = var.validator.memory_mb

  environment {
    variables = merge(
      var.validator.environment,
      {
        APPROVALS_TABLE    = aws_dynamodb_table.approvals.name
        APPROVAL_SNS_TOPIC = aws_sns_topic.approval_requests.arn
      },
      var.trace_log_group_name == null ? {} : { TRACE_LOG_GROUP = var.trace_log_group_name },
    )
  }

  tracing_config {
    mode = "Active"
  }

  kms_key_arn = var.kms_key_arn

  tags = merge(var.tags, {
    Component = "approval-validator"
    Layer     = "approval-gate"
  })
}

# ---------------------------------------------------------------------------
# Executor — the ONLY principal permitted to invoke write tools
#
# It runs after a human has approved and verifies the token before acting. This is the
# component that makes "the model cannot directly cause an irreversible action" true.
# ---------------------------------------------------------------------------

resource "aws_lambda_function" "executor" {
  function_name = "${var.name_prefix}-approval-executor"
  role          = aws_iam_role.executor.arn
  handler       = var.executor.handler
  runtime       = var.executor.runtime
  filename      = var.executor.package_path

  source_code_hash = filebase64sha256(var.executor.package_path)

  timeout     = var.executor.timeout_seconds
  memory_size = var.executor.memory_mb

  # A write executor should not run wide open. Bound it.
  reserved_concurrent_executions = var.executor.reserved_concurrency

  environment {
    variables = merge(
      var.executor.environment,
      {
        APPROVALS_TABLE = aws_dynamodb_table.approvals.name

        # The executor resolves an approved action to a function name by prefixing it.
        # The convention belongs here rather than in tfvars because it is the same
        # convention modules/tools uses to name the functions, and two copies of a naming
        # rule drift.
        WRITE_TOOL_PREFIX = "${var.name_prefix}-tool-"
      },
      var.trace_log_group_name == null ? {} : { TRACE_LOG_GROUP = var.trace_log_group_name },
    )
  }

  tracing_config {
    mode = "Active"
  }

  kms_key_arn = var.kms_key_arn

  tags = merge(var.tags, {
    Component = "approval-executor"
    Layer     = "approval-gate"
  })
}

resource "aws_cloudwatch_log_group" "validator" {
  name              = "/aws/lambda/${aws_lambda_function.validator.function_name}"
  retention_in_days = var.log_retention_days
  kms_key_id        = var.kms_key_arn
  tags              = var.tags
}

resource "aws_cloudwatch_log_group" "executor" {
  name              = "/aws/lambda/${aws_lambda_function.executor.function_name}"
  retention_in_days = var.log_retention_days
  kms_key_id        = var.kms_key_arn
  tags              = var.tags
}
