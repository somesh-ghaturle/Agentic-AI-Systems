# How to deploy

A walkthrough from an existing Snowflake account to a working dev environment, then what
changes for prod. Roughly an hour for dev, most of it spent on the federation setup in
step 2 — which is the part Terraform cannot do on its own behalf.

---

## Before you start

**Required:**

- Terraform ≥ 1.6 (`optional()` in object types, `lifecycle.precondition` on resources)
- A Snowflake account on **Enterprise or above** if you want more than one day of Time
  Travel. Standard caps it at 1, which is fine for dev and not for the approvals table
- A role that can create databases, roles and warehouses at account level. Deliberately
  **not** ACCOUNTADMIN — see below
- Workload identity federation enabled on the account
- A workload identity on the host cloud for each service user

**Not required, and deliberately so:** a private key, a password, or a programmatic access
token. If you find yourself creating one to get started, see "If you cannot use WIF" at the
bottom before you do.

### Why not ACCOUNTADMIN

It works, and it is the fastest way to a green apply. It also means the role that created
your write boundary can trivially undo it, and that every `terraform plan` in CI runs as
the most privileged principal in the account. Create a dedicated role with the three
`CREATE` privileges instead:

```sql
USE ROLE ACCOUNTADMIN;
CREATE ROLE IF NOT EXISTS AGENTIC_DEPLOYER;
GRANT CREATE DATABASE  ON ACCOUNT TO ROLE AGENTIC_DEPLOYER;
GRANT CREATE ROLE      ON ACCOUNT TO ROLE AGENTIC_DEPLOYER;
GRANT CREATE WAREHOUSE ON ACCOUNT TO ROLE AGENTIC_DEPLOYER;
GRANT ROLE AGENTIC_DEPLOYER TO USER <your deployer identity>;
```

`CREATE ROLE` is the uncomfortable one — it is what lets Terraform build the role graph,
and it is also what would let a compromised pipeline build a different one. That is the
argument for the OPA policy and the write-boundary suite running on every change, not an
argument for a smaller grant that cannot do the job.

---

## Step 1 — decide what cannot be changed later

| Decision | Where | Why it is one-way |
|---|---|---|
| Snowflake edition | account | Time Travel > 1 day needs Enterprise |
| `name_prefix` | `locals` in each root | Names every object; renaming recreates all of them, and recreating a role drops every grant made on the old name outside this repo |
| Which cloud hosts the account | `workload_identity_provider` | Determines the WIF block shape; not a Terraform-side choice |
| Archive retention | `archive_retention_days` | From your records policy |

---

## Step 2 — workload identity federation

This is the step that keeps this tree free of credentials, and the one Terraform cannot
bootstrap for itself: something has to authenticate the first apply.

**On the host cloud**, create the identities the handlers will run as. On AWS that is two
IAM roles — one the orchestrator assumes, one the executor assumes. Note their ARNs.

**In Snowflake**, allow federation from your host cloud account. Then the service users
Terraform creates carry a *reference* to those identities rather than a secret:

```hcl
service_users = {
  orchestrator = {
    workload_identity = { aws_role_arn = "arn:aws:iam::123456789012:role/agentic-orchestrator" }
    ...
  }
}
```

**For Terraform itself**, run the apply from a compute context that already holds a
federated identity — a CI runner with an OIDC role, or a workstation with an assumed role.
The provider block names no user:

```hcl
provider "snowflake" {
  authenticator              = "WORKLOAD_IDENTITY"
  workload_identity_provider = "AWS"
  role                       = "AGENTIC_DEPLOYER"
}
```

`user` is deliberately absent. Under `WORKLOAD_IDENTITY` the user is resolved from the
identity presented, and naming one produces a confusing `390144` when the two disagree.

---

## Step 3 — dev

```bash
cd infra/terraform-snowflake/envs/dev
cp terraform.tfvars.example terraform.tfvars   # then edit it
terraform init
terraform plan
terraform apply
```

The plan should create roles, one database, three schemas, a warehouse, the tables, the
procedures, two service users and the grants. It should create **no** secret of any kind.
If you see one, something was configured off this path.

### Then rehearse the boundary

The apply is not the test. Authenticate as the orchestrator identity and try to call a
write procedure directly:

```sql
USE ROLE AGENTIC_DEV_ORCHESTRATOR;
CALL AGENTIC_DEV_DB.TOOLS.PROCESS_REFUND('x', 'order-1', 100);
```

This must fail with insufficient privileges. If it succeeds, stop and read
[README.md](README.md) § "The write boundary" — something in the role graph is not what
this tree assumes.

---

## Step 4 — what prod does differently

| | dev | staging | prod |
|---|---|---|---|
| Time Travel | 1 day | 7 days | 30 days |
| Warehouse | XSMALL, 1 cluster | XSMALL, 1 cluster | `var.warehouse_size`, 3 clusters |
| Network allow-list | none | enforced | enforced, **must be non-empty** |
| Search `target_lag` | 24 hours | 4 hours | 1 hour |
| Sweeper | stopped, 60 min | started, 5 min | started, 5 min |
| `approver_roles` | may be empty | may be empty | **must be non-empty** |

The last row is a root-level `validation` rather than a convention. A production approval
gate with no approver is a gate that can never open, and discovering that from a backlog of
`PENDING` proposals is a worse way to learn it than an apply-time error.

The network allow-list has the same treatment for the opposite reason: an empty list creates
no policy at all, which fails *open*, so prod refuses to accept one.

### Start the sweeper deliberately

`task_started = true` in prod, but the first apply of a new environment should still be
followed by a check that the task is running and its runs are succeeding:

```sql
SELECT NAME, STATE, SCHEDULED_TIME, RETURN_VALUE, ERROR_MESSAGE
  FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(TASK_NAME => 'AGENTIC_PROD_APPROVAL_SWEEPER'))
 ORDER BY SCHEDULED_TIME DESC LIMIT 10;
```

A task that has failed `suspend_after_failures` times in a row suspends itself. That is the
desired behaviour — a task failing every five minutes forever is a warehouse bill with no
output — but it means approvals stop being claimed, silently, until someone looks.

---

## Step 5 — a resource monitor

This tree does not create one, and it should not: a spend cap is an organisational decision,
and a wrong one suspends production. Create it by hand, and know which of the two you want:

```sql
CREATE RESOURCE MONITOR AGENTIC_PROD_RM
  WITH CREDIT_QUOTA = 100
  TRIGGERS ON 80 PERCENT DO NOTIFY
           ON 100 PERCENT DO SUSPEND;      -- or SUSPEND_IMMEDIATE
ALTER WAREHOUSE AGENTIC_PROD_WH SET RESOURCE_MONITOR = AGENTIC_PROD_RM;
```

`SUSPEND` lets running statements finish; `SUSPEND_IMMEDIATE` kills them. For a system
whose write tools are idempotent on an approval ID, `SUSPEND_IMMEDIATE` is survivable —
the stale-claim recovery is exactly the mechanism that picks the work back up.

---

## If you cannot use WIF

Some accounts cannot use workload identity federation yet. Key-pair authentication is the
supported alternative, and it costs this tree its central security property: it introduces
a genuine long-lived secret, the only one in this repository.

If you take that path, take the rotation mechanism with it. Snowflake gives every user two
public-key slots specifically so rotation does not need a cutover window:

```sql
-- 1. Add the new key alongside the old one.
ALTER USER AGENTIC_PROD_ORCHESTRATOR SET RSA_PUBLIC_KEY_2 = '<new public key>';

-- 2. Move every client to the new private key. Both work during this window.

-- 3. Only then, remove the old one.
ALTER USER AGENTIC_PROD_ORCHESTRATOR UNSET RSA_PUBLIC_KEY;

-- 4. Next rotation goes the other way: set RSA_PUBLIC_KEY, unset RSA_PUBLIC_KEY_2.
```

Do not add the private key to `modules/identity`. Terraform would then hold it in state,
which turns one secret into two — see
[../../docs/SECRETS-ROTATION.md](../../docs/SECRETS-ROTATION.md) § 3 for the same problem
in the Azure tree, and why it is an argument against the path rather than a detail of it.
