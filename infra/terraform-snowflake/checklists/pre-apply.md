# Pre-apply checklist

Run before the first prod apply, and again whenever the tool set or the approval flow
changes. Most of these are cheap to check now and expensive to discover later.

---

## Decisions that cannot be undone easily

- [ ] **Snowflake edition** — Enterprise or above? Time Travel beyond 1 day, and therefore
      any meaningful recovery window on the approvals table, requires it
- [ ] **`name_prefix`** — final? It names every role, user, database and warehouse.
      Renaming recreates all of them, and role recreation drops every grant made on the old
      names outside this repo
- [ ] **Which cloud the account sits on** — it determines the WIF block shape in
      `modules/identity`, and it is not a Terraform-side choice
- [ ] **Archive retention** — from your records policy, not from the default

## Identity, before anything else

- [ ] The Terraform role exists and holds `CREATE DATABASE`, `CREATE ROLE` and
      `CREATE WAREHOUSE` at account level — and is **not** ACCOUNTADMIN
- [ ] Workload identity federation is enabled on the account
- [ ] The orchestrator and executor workload identities exist on the host cloud, and their
      ARNs/subjects are the ones in `terraform.tfvars`
- [ ] Nobody has created a key pair "just to get started". A key created now is a key that
      will still be there in a year — see [../../../docs/SECRETS-ROTATION.md](../../../docs/SECRETS-ROTATION.md)

## The write boundary

Verify these against the deployed account, not against the plan. Every one of them is a
valid grant that applies cleanly and looks correct in Snowsight.

- [ ] `SHOW GRANTS TO ROLE <prefix>_ORCHESTRATOR` lists **no** write procedure
- [ ] `SHOW GRANTS TO ROLE <prefix>_ORCHESTRATOR` lists **no** inherited role
- [ ] `SHOW GRANTS OF ROLE <prefix>_EXECUTOR` lists no grant to `<prefix>_ORCHESTRATOR`,
      directly or through any ancestor
- [ ] `SHOW GRANTS TO ROLE <prefix>_TOOL_OWNER` shows the table privileges, and no caller
      role shows them
- [ ] Every procedure in `TOOLS` reports `EXECUTE AS OWNER` — check `SHOW PROCEDURES`
- [ ] The `TOOLS`, `APP` and `AUDIT` schemas report `MANAGED ACCESS`
- [ ] `SHOW GRANTS TO ROLE <prefix>_ORCHESTRATOR` does **not** list `SNOWFLAKE.CORTEX_USER`

```bash
python3 -m unittest discover -s infra/terraform-snowflake/tests -v
```

That suite checks the source. The list above checks the account, which is where a grant
made by hand actually lives.

## The approval gate

- [ ] `approver_roles` names at least one human role, and names **neither** the orchestrator
      nor the executor role
- [ ] Every approver role is granted to a real human user, and those users exist
- [ ] `stale_claim_seconds` exceeds the write tool's own timeout plus its retries
- [ ] Every write tool is idempotent on `APPROVAL_ID` — the stale-claim recovery re-invokes,
      and a tool that ignores its key turns that recovery into a double write
- [ ] `APPROVALS` is a **hybrid** table. A standard table has no row locking and the claim
      can be won twice

## Cost, before it is a surprise

- [ ] `auto_suspend_seconds` is 60, not Snowflake's 600 default
- [ ] `target_lag` on the search service is hours in every environment where nobody queries
      between refreshes
- [ ] `sweep_interval_minutes` reflects the approval latency you actually need — each sweep
      resumes a warehouse
- [ ] A resource monitor exists on the warehouse. This tree does not create one: a spend cap
      is an organisational decision, and a wrong one suspends production

## State and secrets

- [ ] Remote backend configured
- [ ] `terraform.tfvars` is **not** committed
- [ ] No private key anywhere in the configuration or in `TF_VAR_` — if there is one, WIF
      was skipped and this tree's central security property no longer holds

## Network

- [ ] `allowed_ip_list` is non-empty in prod (the root's own validation enforces this)
- [ ] The allow-list covers the host cloud's egress ranges, not just the office
- [ ] An operator can still reach the account if the policy is wrong — it attaches to the
      service users, not the account, but confirm that is still true

## After the first apply

- [ ] The sweeper task is **started** in prod, and its first runs succeeded
      (`SELECT * FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(...))`)
- [ ] The event table is receiving rows
- [ ] Rehearse the boundary: authenticate as the orchestrator and attempt to call a write
      procedure directly. It must fail with insufficient privileges. If it succeeds, stop
      and re-read the write boundary section above
