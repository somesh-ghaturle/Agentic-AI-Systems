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

An approval claim is bound to a fingerprint of the exact action, is single-use, and is enforced
by the validator and executor handlers in [`src/`](../../src/README.md) — which this tree ships,
along with their tests.

**A pending approval never expires.** Nothing in this tree ages one out: the executor's
conditional write accepts a record that is `pending` regardless of age. If an approval request
should lapse after some interval, that is a control you add; it does not exist here today.

**What does have a lifetime is an `executing` claim.** `STALE_CLAIM_SECONDS` (default **900**,
fifteen minutes) is how long a claim may sit in `executing` before another executor may take it
over — recovery for an executor that died between claiming the record and resolving its token.
It is a liveness window, not an authorization expiry, and it is safe only because write tools
are idempotent on the approval ID. It must exceed the write tool's own timeout plus retries.

**How it is set here:** an environment variable on the executor Lambda. There is no Terraform
variable for it in this module — set it through the function's environment block. See
[`src/README.md`](../../src/README.md) for the full environment-variable table.

**What this module does fix:** `aws_dynamodb_table.approvals` carries no TTL, deliberately — the
approval record is evidence, and expiring an audit trail is a records-policy decision rather
than a storage setting.

See [BUILDING-BLOCKS.md](../../../../docs/agentic-system-architecture/BUILDING-BLOCKS.md)
§ "Approval Claim Formats by Cloud" for the claim structure and fingerprint algorithm, and
[SECRETS-ROTATION.md](../../../../docs/SECRETS-ROTATION.md) for what in this stack does rotate.

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
