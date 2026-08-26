# Secrets rotation

What in these four trees is credential material, how each piece rotates, and which pieces
this repository deliberately does not create.

The short version, and the reason this document is shorter than the average rotation guide:
**the Terraform in this repository provisions no long-lived credentials.** There is no
`aws_iam_access_key`, no `google_service_account_key`, no `azuread_application_password`, no
`client_secret`, and no `snowflake_user_public_keys` in any of the `.tf` files. Every workload
authenticates as itself — an execution role on AWS, a user-assigned managed identity on Azure,
a service account on GCP, a federated workload identity on Snowflake — and an identity is
revoked, not rotated.

The Snowflake tree is the one that had to earn that sentence rather than inherit it, and §5 is
about how.

What remains is a short inventory of things that genuinely do rotate, plus one optional secret
per cloud that no environment currently turns on.

---

## 1 · Inventory

| Material | AWS | Azure | GCP | Snowflake |
|---|---|---|---|---|
| Data-at-rest key | `aws_kms_key.main` — [`modules/security/main.tf:33`](../infra/terraform-aws/modules/security/main.tf) | **none** — platform-managed | `google_kms_crypto_key.main` — [`modules/security/main.tf:39`](../infra/terraform-gcp/modules/security/main.tf) | **none** — platform-managed |
| Key rotation | Automatic, annual, AWS-managed | n/a | Automatic, 90 days (`rotation_period`) | n/a |
| Model API key | **none** — Bedrock authenticates by IAM | `azurerm_key_vault_secret.model_key`, optional, **off** | `google_secret_manager_secret.model_key`, optional, **off** | **none** — Cortex runs inside the account |
| Value passes through Terraform state | n/a | **yes** — see §3 | no — container only | n/a |
| Storage account keys | n/a | `shared_access_key_enabled`, off in staging and prod | n/a | n/a |
| How workloads authenticate | Execution role | Managed identity | Service account | **Workload identity federation** — see §5 |
| Static credentials of any kind | none | none | none | none |

Five rows in that table say "none", and they are the load-bearing ones. Rotating a secret you
never created is the cheapest rotation there is.

---

## 2 · Data-at-rest keys

### AWS — annual, automatic, nothing to do

[`aws_kms_key.main`](../infra/terraform-aws/modules/security/main.tf) sets
`enable_key_rotation = true` (line 36). AWS rotates the backing key material once a year and
keeps every previous version, so data encrypted under an older version stays readable. There is
no operator action and no Terraform change. It is not configurable in this module, on purpose:
turning it off is not a choice this repository wants to make easy.

To confirm rotation is on for a deployed key:

```bash
aws kms get-key-rotation-status --key-id alias/<name_prefix>-agentic
```

**Forced rotation.** AWS does not expose on-demand rotation of a symmetric CMK's backing key.
If a key must be retired rather than rotated — suspected compromise of the key policy, not the
key material — the move is to create a new key, re-encrypt, and schedule the old one for
deletion. `key_deletion_window_days` is capped at 30 and defaults to 30 in prod; a key deleted
in error takes its data with it.

### GCP — 90 days, automatic, and the period is yours

[`google_kms_crypto_key.main`](../infra/terraform-gcp/modules/security/main.tf) sets
`rotation_period = var.rotation_period`, which defaults to `"7776000s"` — 90 days. None of
`envs/dev`, `envs/staging`, or `envs/prod` overrides it, so all three run on the default.
Rotation creates a new *primary* version for new encryptions; existing ciphertext stays readable
under the version that wrote it.

Prod runs `protection_level = "HSM"`, dev and staging run `"SOFTWARE"`. HSM key versions cost
more per version and per operation, which is the argument for not shortening the period without
a reason.

To rotate immediately, outside the schedule:

```bash
gcloud kms keys versions create --location <location> \
  --keyring <name_prefix> --key <name_prefix>-key --primary
```

Neither the key nor the key ring can be destroyed — GCP only destroys key *versions*. The module
comments say so at the resource.

### Azure — there is no customer-managed key

This is a real gap, not an omission from this document. The Azure tree contains no
`azurerm_key_vault_key`, no `customer_managed_key` block on any storage account or Cosmos
account, and no `infrastructure_encryption_enabled`. Everything at rest is encrypted under
Microsoft-managed keys, which Microsoft rotates on its own schedule with no customer-visible
control and no customer-visible audit.

The consequence for rotation is that there is nothing to rotate. The consequence for the threat
model is that the Azure tree cannot answer "who could decrypt this, and when did the key last
change" the way the other two trees can. See [THREAT-MODEL.md](THREAT-MODEL.md) for where that
sits among the other per-cloud divergences, and [`infra/MODULES.md`](../infra/MODULES.md) for
the module-by-module comparison.

---

## 3 · The optional model API key

All three trees expose a way to hold a model API key, and **no environment turns it on.** Azure
and GCP set `create_model_key_secret = false` explicitly in each of their `envs/dev`,
`envs/staging`, and `envs/prod` roots; AWS has no such variable at all. (Azure's tenth root,
`envs/tenant`, instantiates only `entra_audit` and holds no secret material.) The default is off
because the default model path on each cloud needs no key:

- **AWS** — Bedrock authorizes by IAM. There is no key, and the module offers no place to put one.
- **GCP** — Claude on Vertex AI authenticates with the caller's own service account.
- **Azure** — Azure OpenAI supports managed identity; the key is for the case where it is not used.

The secret exists for the case where a handler calls a model *outside* the cloud's own service.
If you turn it on, the two clouds behave differently, and the difference decides your rotation
procedure.

### GCP — the value never touches Terraform

[`google_secret_manager_secret.model_key`](../infra/terraform-gcp/modules/security/main.tf)
creates the secret *container* only. There is no `google_secret_manager_secret_version` resource
anywhere in the tree, so the value is added out of band and Terraform never sees it, never
stores it, and never diffs on it.

Rotate by adding a version. No `terraform apply`:

```bash
printf '%s' "$NEW_KEY" | gcloud secrets versions add <name_prefix>-model-api-key --data-file=-
gcloud secrets versions disable <old-version> --secret=<name_prefix>-model-api-key
```

Disable before destroying, and leave it disabled long enough to roll back. Readers resolving the
secret by `latest` pick up the new version on their next fetch; readers pinned to a version
number do not, which is the failure mode to check before disabling the old one.

### Azure — the value passes through Terraform state

[`azurerm_key_vault_secret.model_key`](../infra/terraform-azure/modules/security/main.tf) takes
its value from `var.model_key_secret_value`, which is marked `sensitive` and documented as "pass
via a protected tfvars file or `TF_VAR_`, never in source". `sensitive` suppresses the value in
CLI output. **It does not keep it out of the state file**, which is stored unencrypted-at-the-
Terraform-layer in whatever backend the environment uses.

Rotate by changing the input and applying:

```bash
export TF_VAR_model_key_secret_value="$NEW_KEY"
terraform apply -target=module.security
```

Then treat the state as having held a secret: the previous value remains in the state file's
version history until that history is pruned. If you enable this path, the state backend needs
the same access controls as the vault, and rotating the key means rotating what the backend
retains too. This is the strongest argument for preferring managed identity on Azure and leaving
`create_model_key_secret = false`.

---

## 4 · Azure storage account keys

`shared_access_key_enabled` defaults to `true` in the module and is set to `false` explicitly in
`envs/staging` and `envs/prod` for the archive, tools, and approval storage accounts. Where it
is `false`, the account rejects its own shared keys entirely and every writer authenticates as
itself — there is no key, so there is no rotation.

`envs/dev` does not set it, so dev inherits `true`. Dev's shared keys are live credentials with
no expiry. If dev holds anything worth protecting, either set the flag or rotate on a schedule:

```bash
az storage account keys renew --account-name <account> --key primary
```

Renew one key at a time and let callers pick up the new one before renewing the other; renewing
both at once breaks every reader mid-flight.

---

## 5 · Snowflake, and the credential this repository chose not to create

Snowflake is the only platform of the four with no ambient identity to inherit. A Lambda has an
execution role, a Function App a managed identity, a Cloud Run service a service account — each
supplied by the platform the code runs on. A Snowflake session has whatever the client
authenticated with, and the conventional answer is an RSA private key on disk.

That would have made `terraform-snowflake` the first tree in this repository to provision a
long-lived secret, and would have made the opening sentence of this document false.

**It does not.** [`modules/identity`](../infra/terraform-snowflake/modules/identity/main.tf)
creates `snowflake_service_user` resources whose `default_workload_identity` block names an
external identity — an AWS role ARN, an Azure issuer and subject, a GCP subject, or a generic
OIDC pair. The handler authenticates as that identity on its host cloud and presents it;
Snowflake matches it. Nothing is stored, so nothing leaks and nothing rotates.

Terraform itself authenticates the same way. The provider block in every environment root
carries `authenticator = "WORKLOAD_IDENTITY"` and deliberately no `user`, no `private_key` and
no `token`:

```hcl
provider "snowflake" {
  authenticator              = "WORKLOAD_IDENTITY"
  workload_identity_provider = var.workload_identity_provider
  role                       = var.terraform_role
}
```

### If you cannot use WIF

Some accounts cannot use federation yet. Key-pair auth is supported and documented in
[HOW-TO-DEPLOY.md](../infra/terraform-snowflake/HOW-TO-DEPLOY.md), and taking it means taking
a genuine rotatable secret — the only one this repository would then have.

Snowflake gives every user two public-key slots specifically so that rotation needs no cutover
window. Use both:

```sql
-- 1. Add the new key alongside the old. Both are valid from here.
ALTER USER AGENTIC_PROD_ORCHESTRATOR SET RSA_PUBLIC_KEY_2 = '<new public key>';

-- 2. Move every client to the new private key. Verify before continuing.

-- 3. Only then remove the old one.
ALTER USER AGENTIC_PROD_ORCHESTRATOR UNSET RSA_PUBLIC_KEY;

-- 4. Next rotation runs the other way round: set RSA_PUBLIC_KEY, unset RSA_PUBLIC_KEY_2.
```

Do not put the private key into `modules/identity`. Terraform would hold it in state, turning
one secret into two — the same problem as the Azure model key in §3, and the same argument
against the path rather than a detail of it.

### What Snowflake has instead of a key to rotate

Nothing here expires on a schedule, so there is no rotation calendar. What there is instead is
a revocation surface, and it is worth knowing where it is:

- **Revoke the federation, not a key.** Removing the external identity from the service user,
  or removing the role on the host cloud, ends access immediately and everywhere.
- **The network policy** in `modules/security` is attached to the service users rather than the
  account, so tightening it cannot lock an operator out mid-incident.
- **`CREATE ROLE` on the deploy role** is the largest standing privilege in this tree. It is
  what builds the role graph and therefore what could rebuild it; the OPA policies and the
  write-boundary suite running on every change are the compensating control.

---

## 6 · Approval claims are not secrets, but they do have a lifetime

The approval gate binds authorization to a fingerprint of the exact action. A claim is not a
credential — it is not held, presented, or rotated — so it is out of scope for rotation. It is
covered here only because the question "what expires?" reasonably lands on this page.

The three infrastructure trees ship the validator and executor handlers in `src/`, with tests;
the Snowflake tree implements the same logic as SQL stored procedures in `modules/approval`. The
behaviour below is implemented rather than left to the deployer:

| | Behaviour |
|---|---|
| Pending approval | **Never expires.** The executor's conditional write accepts a `pending` record regardless of age. |
| `executing` claim | Reclaimable after `STALE_CLAIM_SECONDS`, default **900** — recovery for a dead executor, not an authorization expiry. |
| Binding | The executor recomputes the arguments fingerprint and refuses a mismatch. |
| Single use | Enforced by conditional write (DynamoDB condition expression, Cosmos ETag, Firestore transaction, Snowflake `SQLROWCOUNT = 1`). |

GCP and Snowflake expose the window as a Terraform variable (`var.stale_claim_seconds`); AWS and
Azure set it as a handler environment variable. That a pending approval never lapses is a deliberate
gap worth knowing about, not a rotation task.

See [BUILDING-BLOCKS.md](agentic-system-architecture/BUILDING-BLOCKS.md) § "Approval Claim
Formats by Cloud" for the claim structure and fingerprint algorithm.

---

## 7 · CI holds no cloud credentials

[`.github/workflows/checks.yml`](../.github/workflows/checks.yml) declares
`permissions: contents: read` and configures no cloud login — no `aws-actions/configure-aws-credentials`,
no `azure/login`, no `google-github-actions/auth`, and no OIDC (`id-token`) grant. Every job is
static: format, lint, validate, policy, link, and secret scanning. Nothing in CI authenticates
to a cloud, so there is no CI credential to rotate.

This is why `terraform plan` against a real subscription is still open as ENHANCEMENT-PLAN
task 6 rather than merged. Adding it means adding the first cloud credential this repository has
ever needed, and the right form of it is workload identity federation — a short-lived token
minted per run, which keeps this section true.

---

## 8 · Principles

1. **Prefer an identity to a secret.** Every rotation procedure above exists because some path
   could not use one. The paths that could are the reason this document is short.
2. **Never commit a secret**, enforced by `gitleaks` in CI. The rotation procedure for a
   committed secret is not rotation; it is treating the value as public from the commit forward.
3. **Never write a key into HCL.** A `default =` holding a live value is committed by
   definition. Values reach Terraform through `TF_VAR_` or a protected tfvars file that is
   gitignored, and preferably do not reach Terraform at all — see §3.
4. **Overlap, then retire.** Add the new version, confirm readers moved, then disable the old
   one. Disable before destroy, everywhere the API offers both.
5. **Rotating a value does not rotate its copies.** State files, backend version history, and
   local plan output all retain what passed through them.

---

## Related

- [THREAT-MODEL.md](THREAT-MODEL.md) — what a leaked approval claim actually buys an adversary
- [security-checklist.md](security-checklist.md) — the broader control set this sits inside
- [incident-runbook.md](incident-runbook.md) — containment, including credential revocation
- [`infra/MODULES.md`](../infra/MODULES.md) — the per-cloud module catalog
- [`infra/terraform-snowflake/HOW-TO-DEPLOY.md`](../infra/terraform-snowflake/HOW-TO-DEPLOY.md) — the WIF setup, and the key-pair path if you cannot use it
