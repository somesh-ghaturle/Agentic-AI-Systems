# Approval Module (GCP)

This Terraform module implements an approval gate for agentic systems following the principle:
"The model proposes. Application code decides. A human authorizes. The tool executes."

## Overview

The approval gate enforces a strict boundary between read and write operations. It consists of:

1. **Validator Cloud Function** - Application code that validates ownership, permissions, and limits
2. **Executor Cloud Function** - The only principal permitted to invoke write tools
3. **Pub/Sub Topics** - Notification paths for approval requests
4. **Firestore** - Audit record of all approvals

## Components

- `google_cloudfunctions_function.validator` - Validates proposals before human review
- `google_cloudfunctions_function.executor` - Executes approved actions after token verification
- `google_pubsub_topic.approval_requests` - Notifies humans of pending approvals
- `google_firestore_database` - Immutable approval audit trail

## Token Lifetime and Rotation

Approval tokens expire after **24 hours** (configurable via `var.approval_token_ttl_seconds`).

**Rotation:**
1. Generate a new token: `gcloud workflows executions describe <execution-id> --format=json` (or your orchestrator's equivalent)
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
  project_id  = "my-project-123456"
  region     = "us-central1"

  validator = {
    handler       = "validator.handler"
    runtime       = "python312"
    package_path  = "../function/validator.zip"
    timeout_seconds = 30
  }

  executor = {
    handler              = "executor.handler"
    runtime              = "python312"
    package_path         = "../function/executor.zip"
    timeout_seconds      = 60
    reserved_concurrency = 10
  }

  write_tool_uris = [
    "https://us-central1-my-project-123456.cloudfunctions.net/tool-write",
  ]

  labels = {
    Environment = "dev"
    Team        = "platform"
  }
}
```
