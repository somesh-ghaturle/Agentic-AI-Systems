# Migration guide

Adapting the patterns in this repository to a project you already have.

This is written for the common case: an agent that already works, already calls tools, and
already does something in production that someone is nervous about. Nothing here asks you to
start over. The order below is the order that pays off soonest, and each step is useful on its
own — you can stop after step 1 and be meaningfully better off.

If you are starting from nothing, read [CHOOSING-A-TREE.md](../infra/CHOOSING-A-TREE.md)
first and copy [`examples/starter-agent`](../examples/starter-agent/README.md). This guide is
about retrofitting.

---

## Step 0 — Find out which of the six blocks you already have

[BUILDING-BLOCKS.md](agentic-system-architecture/BUILDING-BLOCKS.md) breaks an agentic system
into six. Most working projects have the first three and are missing the last three:

| | Block | Usually present? |
|---|---|---|
| 1 | Model layer and routing | Yes — often one model everywhere, which is fine to start |
| 2 | Tool layer and API contracts | Yes — but rarely with a read/write split |
| 3 | Memory and state | Partly — execution state usually, archive rarely |
| 4 | Orchestration | Yes, implicitly, as a loop in application code |
| 5 | Trace-level evaluation | **Rarely** |
| 6 | Approval gates | **Rarely** |

The gap is almost always 6 first and 5 second. That is the order this guide follows, because
an ungated write path is a present risk while a missing eval harness is a future one.

---

## Step 1 — Put in the write boundary

**This is the one that matters.** Everything else on this page is an improvement; this one is
a control.

The rule is that the part of the system that reasons never gets a handle on the part that
acts. Concretely, in [`hermes-agent`](../examples/hermes-agent/README.md):

```python
read = ToolRegistry(READ)
read.register(Tool("kb_search", READ, "Search the internal knowledge base", _kb_search))
read.register(Tool("service_status", READ, "Read a service's health", _service_status))

write = ToolRegistry(WRITE)
write.register(Tool("restart_service", WRITE, "Restart a service", _restart_service))
write.register(Tool("delete_record", WRITE, "Delete a record", _delete_record))
```

Two registries, not one registry with a flag. The model's loop is handed the read registry
and cannot reach the write one — the boundary is a fact about what the code holds, not a
check it performs.

A write tool returns a **proposal**, never an effect. Something outside the loop approves it,
and only then does anything happen.

### Retrofitting this into an existing agent

1. **List every tool and mark it read or write.** Anything that mutates, spends money, sends a
   message, or is hard to undo is a write. When unsure, call it a write — the cost of being
   wrong in that direction is an extra approval.
2. **Split the registry in two.** This is usually a small change and it is the whole point.
3. **Make write tools return proposals.** They should build a description of the action and
   return it. They should not do it.
4. **Add the approving step outside the model loop.** At first this can be a human at a
   terminal; see step 3 for making it durable.
5. **Write the test that asserts the boundary holds** before you trust it. See step 4.

### Do not infer read-versus-write from the request text

This is the mistake worth naming, because this repository made it and left the evidence in
place. [`graph-agent`](../examples/graph-agent/README.md) classifies by matching phrases, and
its first keyword list contained `"refund"`. The request *"what is the refund policy"* — a
question — matched, routed to the write branch, and drafted a refund for an order the user had
never mentioned.

A noun appears in both a question and a command. A keyword list cannot separate them, and the
failure runs toward the privileged path, which is the worst direction for a mistake to run.

Have the caller name a tool, and register the tool as read or write. `hermes-agent` never
infers intent from a string, which is why it has no equivalent bug to document. Where
`graph-agent` still classifies, it fails *closed* — anything unmatched goes to read — and the
example says so at length, because a graph needs a branch to demonstrate and this is the one
it has.

---

## Step 2 — Add tracing, then evaluate the traces

Once writes are gated you can see what the system is doing.
[`trace-eval`](../examples/trace-eval/README.md) is the reference: it evaluates whole traces
rather than final answers, because an agent that reaches a correct answer through three
unnecessary write attempts is not a correct agent.

Instrument every tool call — read and write — with the action, the arguments, and the outcome.
Then grade the trace, not just the response. The graders in `trace-eval` are ordinary
functions; none of this needs a model or a vendor.

---

## Step 3 — Make approvals durable

An approval gate that lives in memory is a gate that opens when the process restarts.

This is the trap [`graph-agent`](../examples/graph-agent/architecture.md) shipped with: the
graph suspends at `interrupt()`, which is genuinely durable — but only if the checkpointer is.
Hardcoded to an in-memory saver, "approve this tomorrow" quietly meant "keep this Python
process alive overnight". The fix was to make the checkpointer an argument rather than a
source edit, so durability is a deployment choice you can test.

Whatever you use, the property to test is: **a fresh process can resume an approval the
previous one suspended.** If you cannot demonstrate that, you do not have a durable gate.

The claim format matters too. Bind the approval to a fingerprint of the exact action, so that
changing an argument invalidates it — see the approval claim formats in
[BUILDING-BLOCKS.md](agentic-system-architecture/BUILDING-BLOCKS.md#6--approval-gates-and-policy-controls).
Single-use and expiring, or it is a standing permission with extra steps.

---

## Step 4 — Test the boundary, not just the happy path

The tests worth writing are the ones that fail when the control is removed. Each Terraform
tree here ships a suite that asserts its write boundary from the configuration itself, and
they are the model to copy:

```bash
python3 -m unittest discover -s infra/terraform-aws/tests
```

Three kinds of test earn their place:

1. **Boundary tests.** Assert that no write path exists that skips approval. Then break the
   control on purpose and confirm the test fails — a guard you have not seen fail is a guard
   you have not tested.
2. **Trace validation.** Assert every action appears in the trace, including the ones that
   errored.
3. **Recovery.** Kill the process mid-approval and confirm the pending action is still pending
   — not lost, and not applied. [`checkpoint-agent`](../examples/checkpoint-agent/README.md)
   is the reference for resuming idempotently.

---

## Step 5 — Adopt a tree, or borrow from one

Four Terraform trees are here. They are not equivalent, and
[CHOOSING-A-TREE.md](../infra/CHOOSING-A-TREE.md) covers the choice properly. In brief:

| Tree | Write boundary rests on | Worth knowing |
|---|---|---|
| **AWS** | IAM plus a second lock — see [ADR 0001](DECISION-LOGS/0001-dual-lock-aws.md) | Two independent controls; the most defence in depth |
| **GCP** | IAM Deny policies | Strongest single primitive: deny evaluates before allow, so a later broad grant cannot reopen the path |
| **Azure** | `app_role_assignment_required = true` on Function Apps | **One load-bearing line.** `modules/entra-audit` exists to watch it, not to replace it |
| **Snowflake** | Role inheritance | Not a fourth cloud — a data platform. Approvals are *polled*, not called back |

You do not have to adopt a tree wholesale. The common path is to migrate one module at a time
into an existing estate, starting with `modules/approval` and `modules/security`, and leaving
networking and identity where they already are.

Two things surprise people mid-migration:

- **Handler packaging differs by cloud** and is deliberately not unified. Every module reads
  its zip at plan time to compute a deployment hash, so `src/build.sh` has to run before
  `terraform plan` — a tree with unbuilt packages cannot be planned at all.
- **Secrets reach the three trees differently**, and one of them puts a secret value in
  Terraform state. [SECRETS-ROTATION.md](SECRETS-ROTATION.md) says which, and what to do about
  it.

---

## Pitfalls

Ranked by how often they actually bite, and all of them are things that happened here.

**1. Gating the wrong layer.** An approval gate in front of the *model* stops nothing useful —
the model was never the dangerous part. Gate the tool.

**2. An approval that does not survive a restart.** See step 3. It looks like it works right up
until the day it matters.

**3. Inferring intent from text.** See step 1. Fails open, toward the privileged path.

**4. Depending on something you did not declare.** `graph-agent` imported `typing_extensions`
while pinning only `langgraph`, and passed CI for weeks — because the CI environment installed
langgraph, which pulls typing-extensions in transitively. It would have broken for anyone
installing from its requirements file the moment that transitive tree shifted. If you copy an
example, copy its `requirements.txt` and check it actually covers the imports;
`.github/scripts/example_deps.py` is the check that catches this.

**5. Reaching for multi-agent too early.** A single pipeline you can trace beats several agents
you cannot. [`multi-agent-debate`](../examples/multi-agent-debate/README.md) exists partly to
show that even when several agents argue, **none of them holds the write capability** — the
debate produces a proposal, and the same single gate approves it.

**6. Over-trusting one cloud's defaults.** Azure's boundary is one line. GCP's is strong but
only if the deny policy is actually attached. Neither is automatic.

---

## Getting help

- [THREAT-MODEL.md](THREAT-MODEL.md) — what these controls do and do not stop, including the
  assumptions that are weakest
- [MODULES.md](../infra/MODULES.md) — what each Terraform module contains, per cloud
- [DECISION-LOGS](DECISION-LOGS/README.md) — why the choices went the way they did
- Open an issue using one of the [templates](../.github/ISSUE_TEMPLATE) — bug report, feature
  request, or the security template for anything involving the write boundary
