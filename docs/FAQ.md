# Frequently asked questions

Questions that come up more than once, answered against what the repository actually does.
Where a common assumption is wrong, the answer says so rather than working around it.

---

## General

### Can I disable the approval gate for local development?

**There is no switch, and that is deliberate.** No environment variable turns it off, in the
examples or in any of the four Terraform trees.

This surprises people who expect an `APPROVAL_REQUIRED=false`, so it is worth saying why one
does not exist: **the boundary is structural, not conditional.** In
[`hermes-agent`](../examples/hermes-agent/README.md) the model's handler is given a `Toolbelt`
built from the read registry, and the constructor refuses anything else:

```python
if registry.access != READ:
    raise WriteBoundaryViolation(
        "a toolbelt handed to a handler must be built from the read registry"
    )
```

There is no branch to skip because there is no handle to a write tool in the first place. A
flag that disabled this would have to hand the write registry to the model, which is the thing
the design exists to prevent — and a flag that exists in development is a flag that ships.

**What you actually want is almost always one of these.** To see the write path without a human
in the loop, pass `--approve`, which approves that one specific action:

```bash
python3 examples/hermes-agent/agent.py "restart the billing service" --approve
```

To work on a tool without approving anything, register it as a read tool while you develop it.
To test the gate itself, that is what `tests/` is for — the suites assert both directions.

### How do I add a tool to an agent?

Using `hermes-agent` as the reference:

1. **Write the function** in [`hermes/tools.py`](../examples/hermes-agent/hermes/tools.py).
2. **Decide read or write.** Anything that mutates, spends, sends, or is hard to undo is a
   write. When unsure, choose write — an unnecessary approval costs a keystroke, and the
   opposite mistake does not announce itself.
3. **Register it on the matching registry**, not one registry with a flag:

   ```python
   read.register(Tool("service_status", READ, "Read a service's health", _service_status))
   write.register(Tool("restart_service", WRITE, "Restart a service", _restart_service))
   ```

4. **A write tool returns a proposal, never an effect.** The part of the system that reasons
   does not get a handle on the part that acts.
5. **Add a test that fails when the boundary is removed**, not just one that exercises the
   happy path.
6. **Document it** in the example's README.

### Why serverless rather than Kubernetes?

Every tree uses the platform's function runtime — Lambda, Azure Functions, Cloud Functions —
because the unit being secured is *one tool invocation*, and a function is the smallest thing
the cloud will attach an identity to. The write boundary is a grant on that identity. On
Kubernetes the equivalent boundary lands on a service account shared by everything in the pod,
which is a coarser thing to reason about.

It is a valid extension rather than an impossibility. Task 43 in
[ENHANCEMENT-PLAN.md](ENHANCEMENT-PLAN.md) tracks the hybrid case.

### Which tree should I start from?

[CHOOSING-A-TREE.md](../infra/CHOOSING-A-TREE.md) answers this properly. The short version:
GCP has the strongest single primitive (Deny policies evaluate before allow, so a later broad
grant cannot reopen the path), AWS has two independent locks, Azure has one load-bearing line
with an audit module watching it, and Snowflake is not a cloud at all — it is a data platform,
picked when the agent's tools are already queries over data you keep there.

### Are the examples production code?

No. They are the smallest thing that demonstrates one idea, and most are standard library only
so they run with no install and no key. The patterns are production-shaped; the examples are
not production-sized. [MIGRATION-GUIDE.md](MIGRATION-GUIDE.md) covers moving them into
something real.

---

## Security

### Is the write boundary unbreakable?

No, and [THREAT-MODEL.md](THREAT-MODEL.md) is explicit about where it ends — the half about
what is *not* defended is the more useful one.

What it does provide: enforcement at the identity platform (IAM, Entra ID, GCP IAM) rather
than in a prompt or a model's cooperation. That distinction matters because the first kind
holds when the model misbehaves and the second kind is the thing being tested.

Its weakest assumption is documented rather than hidden: the boundary depends on the approval
executor's identity remaining the only principal permitted to invoke write tools. Anyone who
can widen that grant can widen the boundary.

### What if the model ignores its instructions and calls a write tool anyway?

**It cannot name one.** This is worth being precise about, because the usual answer — "the
orchestrator checks the gate before executing" — describes a weaker design than the one here.

The handler is handed a toolbelt built from the read registry. Write tools are not in it, so
there is no name the model can emit that reaches one. A second check inside `call()` refuses a
write tool even if the registry somehow held one:

```python
# Belt and braces: the registry cannot hold a write tool, and this refuses one
# anyway. If the invariant above is ever broken, the failure is this line rather
# than a write executing without an approval.
if tool.access != READ:
    raise WriteBoundaryViolation(...)
```

The model can *ask* for a write. That produces a proposal, and the request stops until a human
approves that exact action.

### Does this stop prompt injection?

It stops prompt injection from *writing*. A model that has been talked into wanting to delete a
record still has only read tools, so the attempt becomes a proposal a human sees.

It does not stop injection from reading, or from lying about what it read. If a read tool can
reach data one user should not see, the boundary does not help — that is an authorization
problem in the tool, and it is one of the cases THREAT-MODEL.md names.

### Where do approval claims come from, and do they expire?

A claim is bound to a **fingerprint of the exact action**, so changing any argument invalidates
it, and it is consumed on use. See the claim formats in
[BUILDING-BLOCKS.md](agentic-system-architecture/BUILDING-BLOCKS.md#6--approval-gates-and-policy-controls).

On expiry, see the troubleshooting answer below — the common belief about it is wrong.

---

## Troubleshooting

### `ModuleNotFoundError` when running an example

Install that example's pinned dependencies:

```bash
pip install -r examples/<example-name>/requirements.txt
```

Most examples need nothing — they are standard library only. Two require Python 3.10+:
`graph-agent` (LangGraph dropped 3.9) and `multi-agent-debate` (`dict | None` in annotations).

### `terraform init` in a tree directory does nothing useful

Because the tree root holds no `.tf` files. Every root is an environment:

```bash
cd infra/terraform-aws/envs/dev
```

### `terraform plan` fails on a missing package

Build the handler packages first. Every module calls `filebase64sha256` on its zip at plan time
to compute a deployment hash, so a tree whose packages are unbuilt cannot be planned at all:

```bash
infra/terraform-aws/src/build.sh
```

Snowflake is the exception — its handler logic is SQL stored procedures, so there is nothing to
build.

### `terraform plan` says a resource already exists

Import it rather than recreating it:

```bash
terraform import <resource_type>.<name> <resource_id>
```

Destroying and recreating is the usual advice and is wrong here for two resources: the archive
bucket and the approvals table hold the audit trail.

### My approval claims keep expiring after 24 hours

**They do not, and nothing in this repository expires them after 24 hours.** This question is
here because the three `modules/approval/README.md` files used to say so, citing a
`var.approval_token_ttl_seconds` that exists in no module. Both were removed. If you are
reading a copy that still mentions either, it predates that fix.

What is actually implemented:

| | Behaviour |
| --- | --- |
| A **pending** approval | Never expires. The executor's conditional write accepts a pending record at any age. |
| An **`executing`** claim | Reclaimable after `STALE_CLAIM_SECONDS`, default 900 — fifteen minutes. |

The fifteen minutes is a **liveness window, not an authorization expiry**: it exists so that an
executor which died mid-action does not hold the claim forever.

How you change it differs by tree, which is worth knowing before you go looking for a variable
that is not there:

| Tree | How to set it |
| --- | --- |
| GCP | `var.stale_claim_seconds` on the approval module |
| Snowflake | `var.stale_claim_seconds`, validated at `>= 60`, and set explicitly to 900 in all three environments |
| AWS | No dedicated variable — pass it through `executor.environment` |
| Azure | No dedicated variable — pass it through the executor's app settings |

On AWS and Azure the handler reads the environment variable and falls back to 900, so leaving
it unset is the same as setting it to 900.

If a claim is genuinely being rejected, the likelier cause is the fingerprint: it binds to the
exact arguments, so a retry with any argument changed is a different action and needs its own
approval.

### An example hangs instead of finishing

It is waiting on stdin. `hermes-agent` and `starter-agent` prompt when given no request, so
run them with one:

```bash
python3 examples/hermes-agent/agent.py "restart the billing service"
```

---

## Still stuck

- [QUICKSTART.md](../QUICKSTART.md) — running something end to end
- [MIGRATION-GUIDE.md](MIGRATION-GUIDE.md) — adapting the patterns to an existing project
- [THREAT-MODEL.md](THREAT-MODEL.md) — what the controls do and do not stop
- [MODULES.md](../infra/MODULES.md) — what each Terraform module contains
- Open an issue with one of the [templates](../.github/ISSUE_TEMPLATE)
