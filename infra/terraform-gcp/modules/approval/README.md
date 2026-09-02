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

- `google_cloudfunctions2_function.validator` - Validates proposals before human review
- `google_cloudfunctions2_function.executor` - Executes approved actions after token verification
- `google_pubsub_topic.approval_requests` - Notifies humans of pending approvals
- `google_firestore_database.approvals` - Immutable approval audit trail

## Token Lifetime and Rotation

An approval claim is bound to a fingerprint of the exact action, is single-use, and is enforced
by the validator and executor handlers in `src/` — which this tree ships, along with their tests
(`src/tests/`).

**A pending approval never expires.** Nothing in this tree ages one out: the executor's
conditional write accepts a record that is `pending` regardless of age. If an approval request
should lapse after some interval, that is a control you add; it does not exist here today.

**What does have a lifetime is an `executing` claim.** `STALE_CLAIM_SECONDS` (default **900**,
fifteen minutes) is how long a claim may sit in `executing` before another executor may take it
over — recovery for an executor that died between claiming the record and resolving its token.
It is a liveness window, not an authorization expiry, and it is safe only because write tools
are idempotent on the approval ID. It must exceed the write tool's own timeout plus retries.

**How it is set here:** `var.stale_claim_seconds` (default 900), wired to the executor's
environment in [`main.tf`](main.tf). This is the only tree of the three that exposes it as a
first-class Terraform variable. The logic lives in
[`src/shared/firestore_io.py`](../../src/shared/firestore_io.py).

**What this module does fix** is the subscription expiry policy — `ttl = ""`, so an approval
subscription never expires out from under a pending request. Unrelated to claim lifetime.

See [BUILDING-BLOCKS.md](../../../../docs/agentic-system-architecture/BUILDING-BLOCKS.md)
§ "Approval Claim Formats by Cloud" for the claim structure and fingerprint algorithm, and
[SECRETS-ROTATION.md](../../../../docs/SECRETS-ROTATION.md) for what in this stack does rotate.

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
