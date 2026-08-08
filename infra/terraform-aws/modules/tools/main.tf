# Tool layer — BUILDING-BLOCKS.md §2
#
# The read/write split is the reason this module exists. From the doc:
#
#   "Read tools can be liberally available. Write tools go through validation and, for
#    high-impact actions, human approval. The model proposes writes; application code
#    decides whether they happen. That inversion is the single most important safety
#    property in the system."
#
# Terraform enforces the half that infrastructure can enforce: a write tool gets a
# distinct IAM role, and only the approval gate's role can invoke it. The other half —
# validating ownership, permissions, and limits — is application code, because
# "the prompt is a hint; the code is the control."
#
# Each tool declared here becomes one Lambda with a timeout (no exceptions, per the doc)
# and a role carrying exactly its own permissions.

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

locals {
  read_tools  = { for k, v in var.tools : k => v if v.access == "read" }
  write_tools = { for k, v in var.tools : k => v if v.access == "write" }
}

resource "aws_lambda_function" "tool" {
  for_each = var.tools

  function_name = "${var.name_prefix}-tool-${each.key}"
  role          = aws_iam_role.tool[each.key].arn
  handler       = each.value.handler
  runtime       = each.value.runtime
  filename      = each.value.package_path

  source_code_hash = filebase64sha256(each.value.package_path)

  # "Timeout — every external call, no exceptions." A tool without one holds a worker
  # until something else breaks.
  timeout     = each.value.timeout_seconds
  memory_size = each.value.memory_mb

  # Bound the concurrency of write tools specifically: agents retry, and an unbounded
  # retry storm against a write path is how a confused agent becomes an incident.
  reserved_concurrent_executions = each.value.reserved_concurrency

  environment {
    variables = merge(
      var.common_environment,
      each.value.environment,
      {
        TOOL_NAME   = each.key
        TOOL_ACCESS = each.value.access
      },
      var.trace_log_group_name == null ? {} : { TRACE_LOG_GROUP = var.trace_log_group_name },
    )
  }

  tracing_config {
    mode = "Active"
  }

  kms_key_arn = var.kms_key_arn

  tags = merge(var.tags, {
    Component  = "tool-${each.key}"
    Layer      = "tool"
    ToolAccess = each.value.access
  })
}

resource "aws_cloudwatch_log_group" "tool" {
  for_each = var.tools

  name              = "/aws/lambda/${var.name_prefix}-tool-${each.key}"
  retention_in_days = var.log_retention_days
  kms_key_id        = var.kms_key_arn

  tags = var.tags
}

# ---------------------------------------------------------------------------
# Per-tool roles — least privilege, one role per tool
#
# "A tool that reads order status does not need write access to the orders table. A tool
# that sends a notification does not need the customer database."
# ---------------------------------------------------------------------------

resource "aws_iam_role" "tool" {
  for_each = var.tools

  name = "${var.name_prefix}-tool-${each.key}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = merge(var.tags, { ToolAccess = each.value.access })
}

resource "aws_iam_role_policy_attachment" "tool_basic" {
  for_each = var.tools

  role       = aws_iam_role.tool[each.key].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Every tool writes to the shared trace log group. That group is where the metric filters
# live, so a tool without this permission runs fine and reports nothing — the worst
# failure mode available, because the alarms stay green.
resource "aws_iam_role_policy" "tool_traces" {
  for_each = var.trace_log_group_arn == null ? {} : var.tools

  name = "${var.name_prefix}-tool-${each.key}-traces"
  role = aws_iam_role.tool[each.key].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["logs:CreateLogStream", "logs:PutLogEvents"]
      Resource = [var.trace_log_group_arn, "${var.trace_log_group_arn}:*"]
    }]
  })
}

# Every tool function encrypts its environment variables with the customer-managed key,
# and Lambda decrypts them using the function's own execution role — not a service
# principal. Without this the function never reaches its handler:
#
#   Lambda was unable to decrypt the environment variables because KMS access was denied.
#
# Every other module that encrypts a Lambda grants this; this one did not.
resource "aws_iam_role_policy" "tool_kms" {
  for_each = var.kms_key_arn == null ? {} : var.tools

  name = "${var.name_prefix}-tool-${each.key}-kms"
  role = aws_iam_role.tool[each.key].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["kms:Decrypt", "kms:GenerateDataKey"]
      Resource = [var.kms_key_arn]
    }]
  })
}

# The caller supplies each tool's data-plane permissions as a policy document. There is no
# sensible default here — the whole point is that permissions are specific to the tool.
resource "aws_iam_role_policy" "tool" {
  for_each = { for k, v in var.tools : k => v if v.policy_json != null }

  name   = "${var.name_prefix}-tool-${each.key}-data"
  role   = aws_iam_role.tool[each.key].id
  policy = each.value.policy_json
}

# ---------------------------------------------------------------------------
# The read/write invocation split
#
# Read tools: the orchestrator calls them directly.
# Write tools: ONLY the approval gate may invoke. The orchestrator can propose a write,
# but it cannot execute one — that is the inversion the architecture depends on.
# ---------------------------------------------------------------------------

resource "aws_lambda_permission" "read_tool_from_orchestrator" {
  for_each = local.read_tools

  statement_id  = "AllowOrchestratorInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.tool[each.key].function_name
  principal     = "states.amazonaws.com"
  source_arn    = var.orchestrator_state_machine_arn

  source_account = data.aws_caller_identity.current.account_id
}

resource "aws_lambda_permission" "write_tool_from_approval" {
  for_each = local.write_tools

  statement_id  = "AllowApprovalGateInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.tool[each.key].function_name
  principal     = "lambda.amazonaws.com"
  source_arn    = var.approval_executor_arn

  source_account = data.aws_caller_identity.current.account_id

  lifecycle {
    precondition {
      condition     = var.approval_executor_arn != null
      error_message = "Write tools are declared but approval_executor_arn is null. A write tool with no approval gate in front of it means the model can execute irreversible actions directly — supply the approval module's executor ARN, or reclassify the tool as read."
    }
  }
}
