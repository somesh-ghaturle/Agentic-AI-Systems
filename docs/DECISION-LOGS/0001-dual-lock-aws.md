# ADR 0001 — Two locks on the AWS write boundary, and only one of them fails the plan

**Status: Accepted** · Decided 2026-08-07 · Amended 2026-08-14 · Scope: `infra/terraform-aws/`

## Context

The claim this repository makes, three times in three clouds:

> A state-changing action cannot reach production without a human approving that specific action.

On AWS that means the orchestrator may *propose* a write and the approval executor is the only
principal that may *invoke* a write tool. Two mechanisms in the tree carry that:

| | Where | What it does |
|---|---|---|
| Resource policy | [`modules/tools/main.tf:193`](../../infra/terraform-aws/modules/tools/main.tf) — `aws_lambda_permission.write_tool_from_approval` | Admits the approval executor's ARN, not `states.amazonaws.com`. Carries a `lifecycle.precondition` that fails the plan when a write tool is declared with `approval_executor_arn == null`. |
| Identity policy | [`modules/orchestration/main.tf:102`](../../infra/terraform-aws/modules/orchestration/main.tf) — the `InvokeToolFunctions` statement | Scopes the state machine's `lambda:InvokeFunction` to `var.tool_function_arns`, which the env roots populate from `module.tools.read_tool_arns`. |

The fact the whole decision turns on: **for a caller in the same account, Lambda authorizes an
invocation if the identity policy allows it OR the resource policy does.** Not AND. The resource
policy cannot deny what the identity policy already permits.

This repository used to claim the AWS tree needed no write-boundary test, because its boundary
was a resource policy and getting it wrong was a plan-time error. That is true of the resource
policy and only of the resource policy.

## Decision

Keep both locks, and treat them as **asymmetric rather than redundant**:

- The resource policy is the grant, and the precondition is the only part of the boundary
  Terraform can fail before anything exists.
- The identity policy is a **bypass**. Nothing in Terraform inspects the contents of
  `tool_function_arns`.

Because nothing inspects that list, add a static check that does:
[`infra/terraform-aws/tests/test_write_boundary.py`](../../infra/terraform-aws/tests/test_write_boundary.py).
It reads the source rather than a plan, so it needs no AWS credentials and runs anywhere:

```bash
python3 -m unittest discover -s infra/terraform-aws/tests
```

## Consequences

- **The mutation being guarded is a one-word edit that reads as a simplification.** Passing
  `module.tools.tool_arns_by_name` instead of `read_tool_arns` hands the state machine direct
  invocation of every write tool. `terraform validate` passes, no precondition fires, and the
  plan shows an IAM statement gaining an ARN. Nothing else in the repository objects.
- Eleven test methods cover that plus the quieter variants: a wildcard `lambda:InvokeFunction`,
  the write tools' resource policy naming `states.amazonaws.com`, the read/write `for_each`
  maps swapping, the precondition being deleted, `source_account` scoping being dropped, and
  `read_tool_arns` losing its `access == "read"` filter.
- Cost: two places that must stay right, and a test coupled to the modules' source that has to
  be updated whenever they are refactored. Accepted deliberately — the alternative is a
  boundary whose failure mode is a green CI run.
- **This shape is AWS-specific.** Azure has no Function resource policy at all, so its boundary
  rests on a single lock, `app_role_assignment_required = true`, compensated by
  `modules/entra-audit` and a CI assertion. See [`docs/THREAT-MODEL.md`](../THREAT-MODEL.md) for
  the per-cloud verdicts.

## Alternatives considered

1. **Resource policy alone, trusting the precondition.** What the repo previously claimed.
   Rejected on 2026-08-14: false for same-account callers, and false in the exact direction
   that matters.
2. **Identity policy alone.** Rejected. It gives up the one boundary error Terraform can catch
   at plan time — a write tool declared with no approval gate in front of it.
3. **Separate AWS accounts for the orchestrator and the write tools.** This converts the OR
   into a cross-account evaluation, where the resource policy *and* the caller's identity
   policy must both allow. Genuinely stronger, and the right answer for a real deployment.
   Rejected here because it makes the reference tree a multi-account exercise before anyone
   can run it once. This is the documented upgrade path, not a rejected idea.
4. **An SCP or permission boundary denying `lambda:InvokeFunction` on the write tool ARNs to
   the orchestrator role.** An explicit Deny does beat the OR. Rejected as a default because it
   requires AWS Organizations and a second artifact maintained alongside the role — worth doing
   in an organization that already has that machinery.

## What would reopen this

Splitting the tree across accounts (alternative 3), or any change to how Lambda evaluates
same-account invocation. If the OR ever becomes an AND, the static test becomes redundant and
should be deleted rather than left as decoration.
