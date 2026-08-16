# Azure infrastructure

A parallel Terraform layout to `infra/terraform-aws`, enforcing the same architecture on Azure primitives.

```
modules/   reusable modules — networking, identity, security, state, archive,
           knowledge, tools, approval, orchestration, observability, model-integration
envs/      environment roots — dev, prod
```

**Start with [HOW-TO-DEPLOY.md](HOW-TO-DEPLOY.md).** It covers prerequisites, the Entra permissions this needs beyond subscription Contributor, what prod does differently, and what is still missing.

---

## Status

`terraform validate` passes in both environments. `terraform plan` needs the deployment packages built first — every function package path is checked with `fileexists()` at plan time — so run `src/build.sh` before planning.

The handler source tree exists at `src/`. It is written against the Azure SDK and the Functions v2 programming model rather than ported line-by-line from `infra/terraform-aws/src`, because three things genuinely differ:

- **The approval claim.** DynamoDB expresses "update only if still pending" as a condition on one call. Cosmos has no conditional update; the equivalent is an ETag with `if_match`, and a 412 is what tells the executor somebody else claimed the record. Drop the ETag and a double-clicked approve button runs the refund twice.
- **Traces go to stdout.** Every alert reads `FunctionAppLogs`, whose `Message` column is the handler's console output — so printing one JSON object per line is exactly right here, and reaching for an SDK would put records where the queries never look. The field is `event_type` and the terminal event is `request_complete`; the GCP tree uses different names for both, and a handler copied from it emits records that parse fine and match no alert.
- **Packaging ships source, not wheels.** `SCM_DO_BUILD_DURING_DEPLOYMENT` hands the zip to Oryx, which installs `requirements.txt` on the build server. Vendoring wheels locally would ship a developer machine's binaries into a Linux app.

Handler logic lives in `handler.py`, with `function_app.py` as a thin binding, so `src/tests/` can import and test it without a running host. See [Remaining work](HOW-TO-DEPLOY.md#remaining-work) for what is left.

---

## The one thing to understand before changing anything

Tools are split into `read` and `write`, and only the approval executor can invoke a write tool. The orchestrator cannot — not "is not supposed to", but cannot obtain a token for one.

On AWS that split is a Lambda resource policy naming a single principal. Azure has no equivalent, so it is built from two Entra facts working together, both in `modules/tools`:

1. `app_role_assignment_required = true` on each tool's service principal. Entra then refuses to issue a token for that resource to any principal without an app role assignment. **This is the load-bearing line.** Set it false and every workload in the tenant can obtain a valid token, and the whole split becomes decorative.
2. Easy Auth (`auth_settings_v2`, `unauthenticated_action = "Return401"`) on the Function App rejects any request without a valid token for that specific audience, before a line of handler code runs.

The invoke role from (1) goes to the orchestrator for read tools and to the approval executor for write tools. Never both.

The tempting shortcut — a function key in an app setting — fails the moment anything can read app settings, appears in logs and diagnostic dumps, cannot be attributed to a caller after the fact, and requires coordinating every caller to rotate. It is not used anywhere here.

---

## Why there is an `identity` module when AWS has none

The enforcement flow is circular: `modules/tools` needs the executor's principal ID to scope its write-tool app role assignment, and the executor needs the write tools' addresses to call them.

On AWS this is broken by computing ARNs in `locals` — resource names are deterministic, so their ARNs are known before the resources exist. Azure has no equivalent trick: a managed identity's principal ID is server-assigned and cannot be predicted.

So the cycle is broken by extraction. `modules/identity` depends on nothing and creates every principal up front; `tools`, `approval`, and `orchestration` all consume identities from it rather than from each other.

---

## Credentials

There are none. No service principal passwords, no storage account keys in app settings, no function keys. Every workload authenticates as its own user-assigned managed identity, and Azure holds and rotates the credential.

An earlier version of `modules/identity` created a service principal password with `end_date_relative = "8760h"`. It sat in Terraform state in plaintext and would have taken the system down silently on its first birthday. If you find yourself adding a secret to make something work, that is the signal to check what identity should have been granted instead.

The Key Vault uses RBAC authorization rather than access policies — role assignments show up in subscription-wide access reviews and in `az role assignment list`, and "Key Vault Secrets User" grants read without granting the ability to overwrite. The access policy it replaced handed out Get/List/Set/Delete in one block.

### Authenticating the Terraform CLI

That covers the workloads. Your own `terraform plan` still needs credentials. Use `az login` for local development, or set `ARM_CLIENT_ID`, `ARM_CLIENT_SECRET`, `ARM_TENANT_ID`, and `ARM_SUBSCRIPTION_ID` from CI — though OIDC federation is preferable to a client secret there, for the same reason this tree gives every workload a managed identity instead of a password.

These notes used to live in a tree-level `providers.tf` that no root ever loaded. Each root under `envs/` declares its own `provider "azurerm"` and `provider "azuread"` blocks; there is no shared one.

---

## Azure OpenAI

`modules/model-integration` deliberately creates nothing. Provisioning an Azure OpenAI account requires tenant-level enrollment that Terraform cannot request, so the account is created out of band and its endpoint is passed in as a variable.

Prefer managed identity over a key. If your deployment requires key auth, set `create_model_key_secret = true` on the security module and supply `model_key_secret_value` through a protected tfvars file or `TF_VAR_`, never in source.
