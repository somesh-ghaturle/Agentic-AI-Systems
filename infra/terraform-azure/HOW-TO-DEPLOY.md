# How to deploy (Azure)

A walkthrough from an empty Azure subscription to a working dev environment, then what changes for prod.

> **Build the packages before planning.** Every function package path is checked with `fileexists()` at plan time, so run `./src/build.sh` first or `terraform plan` stops on the first missing zip. The handlers live in `src/` and are written against the Azure SDK and the Functions v2 programming model — the AWS handlers in `infra/terraform-aws/src` use boto3, DynamoDB, and Step Functions task tokens, and would not run on Azure Functions unmodified. See [Remaining work](#remaining-work) for what is still open.

---

## Before you start

**Required:**
- Azure CLI installed and authenticated:
  ```bash
  az login
  az account set --subscription <SUBSCRIPTION_ID>
  ```
- Terraform ≥ 1.6
- Permissions to create Resource Groups, Storage Accounts, Key Vaults, Cosmos DB accounts, Log Analytics Workspaces, Service Bus Namespaces, Search Services, Function Apps, and Logic Apps in the target subscription.
- **Entra permissions to create app registrations and grant app roles.** This is the one that surprises people. The read/write tool split is enforced by Entra app roles, so `terraform apply` registers one application per tool and assigns roles to managed identities. A subscription Contributor without directory permissions cannot do this — you need at least the *Application Developer* directory role, plus the ability to create app role assignments.

**Decide before the first apply:**
- `project` — combined with the environment into the prefix on every resource name. Changing it later recreates almost everything. Keep it short: Azure caps Cosmos accounts and storage accounts at 24 characters, and the variable validation enforces a limit that keeps the longest generated name inside it.

---

## 1 · Remote state

Local state has no lock. Two people applying at once corrupt each other's work, and nothing stops them. Set this up before a second person touches the environment, and before any prod apply.

```bash
az group create --name agentic-tfstate-rg --location eastus

az storage account create \
  --name agentictfstatesa \
  --resource-group agentic-tfstate-rg \
  --location eastus \
  --sku Standard_LRS \
  --allow-shared-key-access false

az storage container create \
  --name tfstate \
  --account-name agentictfstatesa \
  --auth-mode login
```

Then replace the `backend "local" {}` block in `envs/dev/main.tf` (and `envs/prod/main.tf`) with the commented-out `backend "azurerm"` block directly above it, filling in the names you just created.

`use_azuread_auth = true` in that block is deliberate: it authenticates to the state container as you rather than with a storage account key, which is the same posture the rest of this stack takes.

---

## 2 · Build the function packages

```bash
./src/build.sh
```

Produces one zip per handler in `build/`, which is where the `package_path` values in `terraform.tfvars` point.

Each zip carries `function_app.py` (the v2 binding, discovered by that exact name), `handler.py` (the logic, importable without a host so `src/tests/` can test it), `host.json`, and `requirements.txt`. The script ships source rather than vendoring wheels: `SCM_DO_BUILD_DURING_DEPLOYMENT` hands the zip to Oryx, which runs `pip install` on the build server against the real Linux runtime. Vendoring locally would ship a developer machine's binaries into the app.

An undeclared import is not caught here. It is caught at cold start, on an app that deployed successfully — which is why `build.sh` fails outright on a package missing its `requirements.txt`.

---

## 3 · Configure

```bash
cd envs/dev
cp terraform.tfvars.example terraform.tfvars
```

Fill in at minimum `project` and `subscription_id`. `subscription_id` is required as of azurerm 4.x — the provider no longer infers it from your CLI context, and leaving it out fails at plan with a message that does not mention it.

Then read the `tools` block carefully. The `access` field on each tool decides its invocation path and nothing else in that file matters more:

| `access` | Who may invoke it |
|---|---|
| `read` | The orchestrator holds the invoke app role and calls it directly |
| `write` | **Only** the approval executor holds it — the orchestrator cannot obtain a token |

Classify by what the handler *does*, not by what it is called. A tool named `lookup_account` that also writes an audit row is a write tool. When unsure, classify as write: the cost of an unnecessary gate is one extra click, the cost of a missing one is an irreversible action nobody authorized.

`terraform.tfvars` is gitignored. Keep it that way.

---

## 4 · Apply

```bash
terraform init
terraform validate
terraform plan
terraform apply
```

Entra propagation is eventually consistent. If the first apply fails on an app role assignment or a Key Vault secret with a 403, re-running usually succeeds — the assignment existed but the data plane had not seen it yet.

---

## 5 · What prod does differently

Same modules, same wiring, same order. Every difference is a variable value:

| | dev | prod |
|---|---|---|
| Function plans | Consumption (`Y1`) | Elastic Premium (`EP1`) |
| Service Bus | Standard | Premium, local auth off |
| Approval records | no PITR | continuous backup on |
| Key Vault | purge protection off, 7-day retention | purge protection **on**, 90-day retention |
| Storage shared keys | enabled | disabled |
| Storage replication | LRS | ZRS (state, tools, approval), GRS (archive) |
| Log retention | 30 days | 365 days |
| Trace archive | expires at 90 days | tiers to archive, expires at 7 years |

The `EP1` plan in prod is not about performance. Consumption plans cannot join a VNet, so every private-endpoint variable in this stack is unusable on `Y1`. Prod pays for Elastic Premium to keep that door open.

---

## 6 · Component mapping

| Module | Azure services | AWS analogue |
|---|---|---|
| `networking` | Resource Group, VNet, subnet | VPC |
| `identity` | User-assigned managed identities | IAM roles |
| `security` | Key Vault with RBAC authorization | KMS + IAM |
| `state` | Storage Table (`executionstate`) | DynamoDB |
| `archive` | Blob container with lifecycle policy | S3 + lifecycle rules |
| `knowledge` | Azure AI Search | OpenSearch Serverless |
| `tools` | One Function App per tool, one Entra app registration each | Lambda per tool |
| `approval` | Cosmos DB + Service Bus + validator/executor Function Apps | DynamoDB + SQS + Lambda |
| `orchestration` | Logic App workflow | Step Functions |
| `observability` | Log Analytics workspace | CloudWatch |

Two mappings are worth explaining because the obvious choice was rejected:

**Cosmos DB, not Table Storage, for approval records.** The executor claims a pending approval with a conditional write, so that a double-clicked approve button cannot execute twice. Cosmos provides ETag/If-Match optimistic concurrency — the direct analogue of DynamoDB's `ConditionExpression`. Table Storage has no equivalent. The account is also set to Strong consistency deliberately: under eventual consistency a second executor can read a stale `pending` and claim an already-claimed record, which is the exact double-execution the gate exists to prevent.

**Managed identities, not a service principal with a password.** An earlier version of the identity module created a service principal password with a one-year expiry. It lived in Terraform state in plaintext, had to be rotated by hand, and would have taken the system down silently on its first birthday. Azure holds a managed identity's credential, rotates it, and never shows it to you or to the workload.

---

## Remaining work

Before this can be applied to a real subscription:

1. **The Logic App workflow definition.** `modules/orchestration` creates the workflow and attaches the orchestrator identity, but the workflow body — call retrieve, call the model step, call the validator, suspend on the approval callback — is not written. Without it there is no orchestrator, only the identity one would run as.
2. **Trace emission from the handlers.** `modules/observability` creates the workspace, routes the function apps and the Logic App into it with diagnostic settings, and defines five alert rules — loop bound, schema failures, abandoned approvals, daily cost, and the Entra write-boundary audit. Every one of them reads `FunctionAppLogs` and parses the `Message` column as JSON, so they stay at zero until handlers actually emit structured traces. `src/shared/agentic_trace.py` does that, and `src/tests/` asserts the field names match; what is untested is the end-to-end path, which needs a real deployment.
3. **Globally unique resource names.** Key Vault, Cosmos, and every storage account name in this stack is derived deterministically from `project`. Those namespaces are global to Azure, not scoped to your subscription, so two teams using the same `project` value collide at apply time.
4. **Private endpoints.** `modules/knowledge` provisions one; Cosmos, Service Bus, Key Vault, and the OpenAI account do not have one yet. Every `*_public_network_access_enabled` variable therefore still defaults to `true`, and closing them needs both the endpoints and a function plan that can join the VNet — the Y1 consumption plan used in dev cannot.
5. **Cosmos local auth.** Account keys should be disabled. The provider attribute that did this is deprecated and its replacement is not pinned in this repo's provider version, so it is deliberately left unset rather than guessed at. Enforce it with the Azure Policy *"Cosmos DB database accounts should have local authentication methods disabled"* in the meantime.

---

## Troubleshooting

**`Insufficient privileges to complete the operation`** during apply — you have subscription rights but not directory rights. The tools module registers Entra applications. See [Before you start](#before-you-start).

**Storage account name errors** — Azure storage account names are globally unique, lowercase, alphanumeric, 3–24 characters. Shorten `project`.

**`403` from Key Vault on the first apply** — RBAC role assignments are eventually consistent, and Terraform considers one created before Key Vault's data plane has seen it. Re-run.

**Function App fails to start with a storage connection error** — check that `AzureWebJobsStorage__credential` and `AzureWebJobsStorage__clientId` are present in its app settings. `storage_uses_managed_identity` alone points the runtime at a *system*-assigned identity, which these apps do not have.
