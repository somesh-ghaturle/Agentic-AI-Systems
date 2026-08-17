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

- `azurerm_function_app.validator` - Validates proposals before human review
- `azurerm_function_app.executor` - Executes approved actions after token verification
- `azurerm_eventgrid_topic.approval_requests` - Notifies humans of pending approvals
- `azurerm_cosmosdb_account` - Stores immutable approval audit trail

## Token Lifetime and Rotation

Approval tokens expire after **24 hours** (configurable via `var.approval_token_ttl_seconds`).

**Rotation:**
1. Generate a new token: `az durable-functions task-token get --task-token <token>` (or your orchestrator's equivalent)
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
