# Snowflake infrastructure

A fourth Terraform layout alongside `infra/terraform-aws`, `infra/terraform-azure` and
`infra/terraform-gcp`, enforcing the same architecture on Snowflake primitives.

```
modules/   reusable modules — state, security, identity, model, knowledge,
           tools, approval, orchestration, observability, archive
envs/      environment roots — dev, staging, prod
tests/     static checks on the write boundary, no credentials required
```

**Start with [HOW-TO-DEPLOY.md](HOW-TO-DEPLOY.md).** It covers the account prerequisites,
the workload identity federation setup Terraform cannot perform on itself, what prod does
differently, and how to rehearse the write boundary before trusting it.

---

## Snowflake is not a fourth cloud, and this tree does not pretend otherwise

The other three trees target infrastructure providers. Snowflake is a data platform that
*runs on* one of them — it has no VPC, no cloud IAM, and no general-purpose compute. Every
architectural difference in this tree traces back to that, and the honest ones are worth
reading before the code:

| | The other three | Here |
|---|---|---|
| Compute | Lambda / Functions / Cloud Run | Stored procedures |
| Write boundary | Resource policy / deny policy / app-role flag | The role graph |
| Orchestration | Step Functions / Durable Functions / Workflows | A scheduled Task — **no suspend-and-resume** |
| Identity | Ambient (execution role, managed identity, service account) | Workload identity federation |
| Network isolation | VPC / VNet / VPC-SC | Account-level allow-list only |
| Model | Bedrock / Azure OpenAI / Vertex | Cortex |

The row that costs the most is orchestration. A Task is a scheduler, not a workflow engine:
it cannot suspend an execution awaiting a human and resume it on a callback. So the
approval path here is a poll — a proposal sits `APPROVED` until the sweeper next looks.
The write boundary is unaffected, because a boundary made of grants does not care how the
executor was woken. Latency and warehouse cost are affected, and
`sweep_interval_minutes` is the lever. See [modules/orchestration](modules/orchestration/main.tf).

## Status

`terraform validate` passes in all three environments. Nothing here has been applied — the
same status every other root in this repository has.

`terraform plan` needs a Snowflake account and a federated identity that can reach it. It
does not need a private key: see the next section, which is the one genuine security
divergence in this tree and the reason it was built the way it was.

## No credential, by construction

The other three trees inherit an ambient identity from the platform their code runs on. A
Snowflake session has no such thing — historically that meant an RSA private key on disk,
which would have made this the first tree in the repository to provision a long-lived
secret.

It does not. Every service user here carries a *federated identity* rather than a
credential: a statement about which AWS role, Azure managed identity or GCP service
account may become it. There is no key to leak and therefore none to rotate, and
[docs/SECRETS-ROTATION.md](../../docs/SECRETS-ROTATION.md) stays true with a fourth tree in
the repository.

Key-pair authentication is real, supported, and documented in
[HOW-TO-DEPLOY.md](HOW-TO-DEPLOY.md) for accounts that cannot use WIF yet. It costs a
genuine rotatable secret. `modules/identity` does not create one and should not be
extended to.

## The write boundary

```
ORCHESTRATOR ──USAGE──> read procedures          ungated, by design
             ──USAGE──> SUBMIT_PROPOSAL          proposes; cannot approve
             ──USAGE──> COMPLETE_GUARDED         the only model path it holds

  (no edge)  ─ ─X─ ─ ─> write procedures         the boundary

EXECUTOR     ──USAGE──> CLAIM_APPROVAL           single-use, fingerprint-bound
             ──USAGE──> write procedures         the only role that holds these

TOOL_OWNER   ──owns───> every procedure          granted to no user, ever
             ──SELECT/INSERT/UPDATE──> tables    no caller role holds these
```

Two properties make that hold, and both are easy to break with a valid grant:

1. **`EXECUTE AS OWNER` on every procedure.** The caller needs only USAGE; the body runs
   with `TOOL_OWNER`'s privileges. So no caller role holds a table privilege, and the
   grants above are the complete story rather than a summary of it.
2. **The role graph is a forest.** `ORCHESTRATOR` and `EXECUTOR` share no ancestor.
   Snowflake roles inherit transitively, so a single `GRANT ROLE EXECUTOR TO ROLE
   ORCHESTRATOR` — one line, valid, in neither module — hands over every write tool at
   once.

[`tests/test_write_boundary.py`](tests/test_write_boundary.py) guards both, plus five
failure modes that `terraform validate` cannot see. It walks the role graph transitively
rather than checking pairs, because `modules/orchestration` legitimately adds an
inheritance edge and a blocklist would either forbid that or miss the dangerous ones.

```bash
python3 -m unittest discover -s infra/terraform-snowflake/tests -v
```

## Cost, which on this platform is a design input

Snowflake bills compute by the second while a warehouse is resumed. Three settings here
are cost decisions rather than performance ones, and each is commented where it lives:

- `auto_suspend_seconds = 60` in `modules/state` — Snowflake's own default is 600, and ten
  idle minutes after every short agent run is the largest avoidable cost in the stack.
- `target_lag` in `modules/knowledge` — the Cortex Search index refreshes on a warehouse.
  A one-minute lag on a table nobody queries is a warehouse resuming every minute forever.
- `sweep_interval_minutes` in `modules/orchestration` — every sweep resumes a warehouse.
  This trades approval latency directly against standing cost.

## Related

- [ARCHITECTURE.md](ARCHITECTURE.md) — the layer diagram and how the boundary is drawn
- [HOW-TO-DEPLOY.md](HOW-TO-DEPLOY.md) — prerequisites, WIF setup, and the prod differences
- [checklists/pre-apply.md](checklists/pre-apply.md) — what to check before the first apply
- [../MODULES.md](../MODULES.md) — the module catalog across all four trees
- [../CHOOSING-A-TREE.md](../CHOOSING-A-TREE.md) — which tree to start from
