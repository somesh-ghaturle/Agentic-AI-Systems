# Approval Module (Azure)

This Terraform module implements an approval gate for agentic systems following the principle:
"The model proposes. Application code decides. A human authorizes. The tool executes."

## Overview

The approval gate enforces a strict boundary between read and write operations. It consists of:

1. **Validator Function** - Application code that validates ownership, permissions, and limits
2. **Executor Function** - The only principal permitted to invoke write tools
3. **Event Grid Topics** - Notification paths for approval requests
4. **Cosmos DB** - Audit record of all approvals

## Components

- `azurerm_linux_function_app.approval` - Single function app hosting both the validator and executor handlers
- `azurerm_servicebus_topic.approval` - Notifies humans of pending approvals (via Service Bus, not Event Grid)
- `azurerm_cosmosdb_account.approvals` - Stores immutable approval audit trail
- `azuread_application.validator`/`azuread_application.executor` - Entra app registrations with app-role enforcement

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

**How it is set here:** through `var.executor_app_settings`, the generic app-settings map, whose
description names `STALE_CLAIM_SECONDS` as its example. There is no dedicated Terraform variable.
The logic lives in [`src/shared/cosmos_io.py`](../../src/shared/cosmos_io.py).

**What this module does expose** is `var.approval_record_ttl_seconds`, which is a different
thing: the Cosmos `default_ttl` on the approval *records*. It defaults to null — never expire —
because that container is the audit trail.

See [BUILDING-BLOCKS.md](../../../../docs/agentic-system-architecture/BUILDING-BLOCKS.md)
§ "Approval Claim Formats by Cloud" for the claim structure and fingerprint algorithm, and
[SECRETS-ROTATION.md](../../../../docs/SECRETS-ROTATION.md) for what in this stack does rotate.

## Usage

```hcl
module "approval" {
  source = "../modules/approval"

  name_prefix = "myapp-dev"
  location   = "eastus"

  validator = {
    handler       = "validator.handler"
    runtime       = "python3.12"
    package_path  = "../function/validator.zip"
    timeout_seconds = 30
  }

  executor = {
    handler              = "executor.handler"
    runtime              = "python3.12"
    package_path         = "../function/executor.zip"
    timeout_seconds      = 60
    reserved_concurrency = 10
  }

  write_tool_ids = [
    "/subscriptions/.../resourceGroups/.../providers/Microsoft.Logic/workflows/tool-write",
  ]

  tags = {
    Environment = "dev"
    Team        = "platform"
  }
}
```
