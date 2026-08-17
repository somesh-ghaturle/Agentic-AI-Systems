# Approval Module (AWS)

This Terraform module implements an approval gate for agentic systems following the principle:
"The model proposes. Application code decides. A human authorizes. The tool executes."

## Overview

The approval gate enforces a strict boundary between read and write operations. It consists of:

1. **Validator Lambda** - Application code that validates ownership, permissions, and limits
2. **Executor Lambda** - The only principal permitted to invoke write tools
3. **SNS Topics** - Notification paths for approval requests and delivery failures
4. **DynamoDB Table** - Audit record of all approvals

## Components

- `aws_lambda_function.validator` - Validates proposals before human review
- `aws_lambda_function.executor` - Executes approved actions after token verification
- `aws_sns_topic.approval_requests` - Notifies humans of pending approvals
- `aws_sns_topic.approval_delivery_failures` - Alerts on notification failures
- `aws_dynamodb_table.approvals` - Immutable audit trail

## Token Lifetime and Rotation

Approval tokens expire after **24 hours** (configurable via `var.approval_token_ttl_seconds`).

**Rotation:**
1. Generate a new token: `aws stepfunctions get-task-token --task-token <token>` (or your orchestrator's equivalent)
2. Update the orchestrator's environment variable: `APPROVAL_TOKEN=...`
3. Restart the orchestrator

**Mid-execution behavior:** If a token expires during an approval flow, the action is **rejected**
and must be resubmitted with a fresh token. The system logs the expiration and returns a
403 Forbidden to the caller.

**Security note:** Tokens are single-use and bound to a specific action fingerprint.

## Usage

```hcl
module "approval" {
  source = "../modules/approval"

  name_prefix = "myapp-dev"

  validator = {
    handler       = "validator.handler"
    runtime       = "python3.12"
    package_path  = "../lambda/validator.zip"
    timeout_seconds = 30
  }

  executor = {
    handler              = "executor.handler"
    runtime              = "python3.12"
    package_path         = "../lambda/executor.zip"
    timeout_seconds      = 60
    reserved_concurrency = 10
  }

  write_tool_arns = [
    "arn:aws:lambda:us-east-1:123456789012:function:myapp-dev-tool-write",
  ]

  kms_key_arn = "arn:aws:kms:us-east-1:123456789012:key/abcd1234-5678-90ef-ghij-1234567890ab"
  tags = {
    Environment = "dev"
    Team        = "platform"
  }
}
```
