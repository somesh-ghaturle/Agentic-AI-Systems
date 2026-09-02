# multi-agent-debate

Several agents argue about a proposal. The debate makes the proposal better and records what
was never resolved — and it does **not** approve anything.

Requires Python 3.10+ — the `debate/transcript.py` and `debate/panel.py` modules use `X | Y`
union syntax in type annotations. The repository-wide floor is 3.9 for the zero-dependency
examples; this is one of the exceptions, alongside `graph-agent` and `e2e-agent`.

```bash
python3 agent.py                                          # the demo, three outcomes
python3 -m unittest tests.test_multi_agent_debate -v      # from the repository root
```

No dependencies, no model, no key.

## The mistake this example is built to avoid

The natural third role in a debate is an approver: proposer argues, critic objects, approver
decides. It is the obvious design and it quietly destroys the property the rest of this
repository exists to protect.

An agent that approves an agent's proposal is not an authorization step. It is the same
untrusted output wearing a different hat. Every guarantee the approval gate provides — that a
state-changing action cannot reach production without a *human* authorizing that specific
action — is gone the moment the approving principal is another model. The Terraform says so
directly: in all four trees the executor role is deliberately never granted the approve
capability, because a machine role that can approve its own proposal collapses the gate into
a formality.

So a `Verdict` here carries no approval. `requires_human_approval` is a read-only property
that is always `True`, with no constructor argument that changes it — a flag that can be set
is a flag that will be.

What a debate *is* worth: a proposal that survived scrutiny, and an honest record of the
objections it did not answer. Both are useful to the human who still has to approve it.

## What the protocol guarantees

| Guarantee | What it prevents |
| --- | --- |
| `Verdict` has no approval field | A debate being mistaken for an authorization |
| Running out of rounds sets `converged=False` | Exhaustion being reported as agreement |
| Unanswered objections become `dissent` | Consensus manufactured by dropping the objector |
| The transcript closes with the verdict | History rewritten once the outcome is known |
| A panel needs ≥2 critics with distinct perspectives | One opinion reported three times reading as corroboration |
| The arbiter may not propose or oppose | The debate ending when the proposer satisfies themself |

The last two are the ones people are surprised by, and they are the two that make the
difference between a debate and a ritual.

**A panel of clones measures nothing.** Run the same model with the same prompt three times
and unanimous support is not three agreeing opinions; it is one opinion sampled three times.
`Panel` refuses to build itself from critics that declare the same `perspective`.

**An arbiter that argues is not judging.** If whoever calls convergence is also advancing a
position, the debate ends when that participant is satisfied with their own proposal. This is
the write boundary's separation between the principal that proposes and the principal that
authorizes, one layer up — and it is enforced here for the same reason: it is invisible when
it is wrong.

## Layout

```text
debate/
├── verdict.py     what a debate produces, and the approval it deliberately omits
├── transcript.py  the append-only record; frozen turns, one-way close
├── panel.py       the three roles, and the two ways a panel is worse than none
└── protocol.py    the bounded loop, and the three ways it can end
```

Read `verdict.py` first. It is the shortest module and it carries the decision the other
three are arranged around.

## The three endings

`run_debate` distinguishes them, and the distinction is the point — a non-converged verdict
and a converged one must not look identical downstream.

| `converged` | `dissent` | What happened |
| --- | --- | --- |
| `True` | empty | Every critic ended on SUPPORT. Actual agreement. |
| `True` | non-empty | The arbiter called it with objections outstanding. |
| `False` | non-empty | The round budget ran out, or the proposer declined to revise further. |

All three still require a human to authorize the action.

## Why the participants are scripted

The same reason [harness-agent](../harness-agent/README.md) has no model and
[trace-eval](../trace-eval/README.md) uses fixed graders: a debate protocol's guarantees are
properties of *the protocol*. It either records surviving dissent or it does not; it either
stops at the budget or it does not. Putting a model behind the roles would make every run
different without testing anything extra, and would make the suite need a key.

Swapping in real model calls means implementing the three `Protocol` classes in
`debate/panel.py`. Nothing else changes.

## Security

This example makes no security claim, which is why `SECURITY.md` lists it out of scope.

That deserves a sentence, because this example talks about the approval gate more than most.
It models *why* a debate must not authorize, and it enforces that within its own types — but
nothing here is the gate. The gate is `hermes-agent` in application code and
`infra/*/modules/approval` in Terraform. A `Verdict` from this package is an input to that
gate; treating it as a substitute would be exactly the mistake the package is written to
describe.

## Related

- [architecture.md](architecture.md) — the loop, the role separation, and where this sits
  relative to the approval gate
- [hermes-agent](../hermes-agent/README.md) — the write boundary in application code
- [../../docs/agentic-system-architecture/BUILDING-BLOCKS.md](../../docs/agentic-system-architecture/BUILDING-BLOCKS.md)
  §6 — approval gates, and why the authorizing principal must be human
