# IAM for the approval gate.
#
# The split between these two roles is the control. The validator can propose and notify
# but cannot execute; the executor can execute but only resolves tokens it was handed.
# Merging them into one role would collapse two steps of the enforcement flow.

resource "aws_iam_role" "validator" {
  name = "${var.name_prefix}-approval-validator"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = var.tags
}

resource "aws_iam_role" "executor" {
  name = "${var.name_prefix}-approval-executor"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "validator_basic" {
  role       = aws_iam_role.validator.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "executor_basic" {
  role       = aws_iam_role.executor.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "validator" {
  # Writes the proposal and its validation result. No UpdateItem: the validator records
  # what it decided and does not revise history afterward.
  statement {
    sid       = "RecordProposal"
    effect    = "Allow"
    actions   = ["dynamodb:PutItem", "dynamodb:GetItem"]
    resources = [aws_dynamodb_table.approvals.arn]
  }

  statement {
    sid       = "NotifyApprovers"
    effect    = "Allow"
    actions   = ["sns:Publish"]
    resources = [aws_sns_topic.approval_requests.arn]
  }

  # Lets the validator reject an invalid proposal immediately rather than troubling a
  # human with something application code already knows is not allowed.
  dynamic "statement" {
    for_each = var.orchestrator_state_machine_arn == null ? [] : [1]
    content {
      sid       = "RejectInvalidProposal"
      effect    = "Allow"
      actions   = ["states:SendTaskFailure"]
      resources = [var.orchestrator_state_machine_arn]
    }
  }

  dynamic "statement" {
    for_each = var.trace_log_group_arn == null ? [] : [1]
    content {
      sid       = "WriteTraces"
      effect    = "Allow"
      actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
      resources = [var.trace_log_group_arn, "${var.trace_log_group_arn}:*"]
    }
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

data "aws_iam_policy_document" "executor" {
  # Records the outcome against the existing approval record.
  statement {
    sid       = "RecordOutcome"
    effect    = "Allow"
    actions   = ["dynamodb:GetItem", "dynamodb:UpdateItem"]
    resources = [aws_dynamodb_table.approvals.arn]
  }

  # The write tools it is permitted to execute — enumerated, never wildcarded. This list
  # is the definition of what a human approval can authorize in this system.
  dynamic "statement" {
    for_each = length(var.write_tool_arns) > 0 ? [1] : []
    content {
      sid       = "ExecuteApprovedWrites"
      effect    = "Allow"
      actions   = ["lambda:InvokeFunction"]
      resources = var.write_tool_arns
    }
  }

  # Resumes the blocked state machine once the write completes or fails.
  dynamic "statement" {
    for_each = var.orchestrator_state_machine_arn == null ? [] : [1]
    content {
      sid       = "ResolveTaskToken"
      effect    = "Allow"
      actions   = ["states:SendTaskSuccess", "states:SendTaskFailure"]
      resources = [var.orchestrator_state_machine_arn]
    }
  }

  dynamic "statement" {
    for_each = var.trace_log_group_arn == null ? [] : [1]
    content {
      sid       = "WriteTraces"
      effect    = "Allow"
      actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
      resources = [var.trace_log_group_arn, "${var.trace_log_group_arn}:*"]
    }
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

resource "aws_iam_role_policy" "validator" {
  name   = "${var.name_prefix}-approval-validator"
  role   = aws_iam_role.validator.id
  policy = data.aws_iam_policy_document.validator.json
}

resource "aws_iam_role_policy" "executor" {
  name   = "${var.name_prefix}-approval-executor"
  role   = aws_iam_role.executor.id
  policy = data.aws_iam_policy_document.executor.json
}
