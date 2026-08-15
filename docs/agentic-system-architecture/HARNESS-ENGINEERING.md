# Harness engineering

The harness is everything around the model: what assembles its context, what mediates its
tools, what runs its loop, and what decides it is finished. The model is the part that gets
discussed; the harness is the part that determines whether the system works.

This document is about the fourth of those — the part that survives across context windows —
because its failures are the quiet ones. A model that cannot reach a tool gets an error. A
model that declares premature victory gets agreement.

Runnable counterpart: [harness-agent](../../examples/harness-agent/README.md).

---

## 1 · What a harness is responsible for

| Responsibility | The question it answers |
| --- | --- |
| Context assembly | What does the model see this turn? |
| Tool mediation | What can it do, and what happens between the call and the effect? |
| Loop control | When does it get another turn? |
| State and continuity | What survives when the context window ends? |
| Completion | Who decides the work is done? |

The first is [context engineering](CONTEXT-ENGINEERING.md) and large enough to have its own
document. The second is [§2 tool layer](BUILDING-BLOCKS.md) and [§6 approval gates](BUILDING-BLOCKS.md).
The third is the bounded-loop material in [ARCHITECTURE-PATTERNS.md](ARCHITECTURE-PATTERNS.md).

The last two are what follow.

---

## 2 · The agent is not a reliable narrator of its own progress

This is the load-bearing claim, and everything structural comes out of it.

Ask a model whether the task is complete and it will answer. The answer is generated under the
same objective as the rest of its output — plausibility — and it arrives with no more evidential
weight than any other sentence. It may well be correct. It is not *checkable* by being read.

A harness that accepts the model's account of its own progress has no verification step. It has
a ritual that resembles one, which is worse than nothing, because it produces an artifact —
"verified: yes" — that a human downstream will reasonably treat as evidence.

The structural answer is to move the decision out of reach:

- **Completion is a fact about recorded state**, not an assertion. Something the harness owns
  says which features are complete, and `finish` reads that thing.
- **Evidence is produced by the harness**, not the model. A test's exit code, a type checker,
  an end-to-end run. The model can cause evidence to exist by writing working code; it cannot
  author the evidence itself.
- **The transition is refused, not discouraged.** "Please verify before marking complete" is a
  prompt. A state machine where `COMPLETE` is unreachable from `CLAIMED` is a harness.

This is the same principle as "model proposes, code decides" from
[BUILDING-BLOCKS §6](BUILDING-BLOCKS.md), applied to completion instead of authorization.

---

## 3 · Four failure modes

Named in Anthropic's [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents),
which is the primary source for this section.

### Premature completion

The agent declares the project finished with features unimplemented. Common because "done" is
a satisfying thing to output and nothing contradicts it.

**Structural answer:** an explicit feature list, written down before work starts, with per-item
state. Completion is `all(state == COMPLETE)`, evaluated by the harness.

### Over-ambition

The agent attempts too much at once and exhausts its context mid-implementation, leaving several
features half-done and none finished. The next session inherits a mess it has to diagnose before
it can do anything.

**Structural answer:** one unit of work per context window, enforced. Not a request in the
prompt — a claim function that raises the second time it is called.

### Incomplete testing

Features marked complete without end-to-end validation. Distinct from premature completion:
here the agent believes each individual claim, and each individual claim is unverified.

**Structural answer:** the verifier is owned by the harness and consulted by the harness. A
feature with no check defined **fails** rather than passes — otherwise adding a feature and
forgetting its test silently marks it done.

### State degradation

The environment is left with undocumented breakage or partial implementations, so each session
starts further from a clean base than the last.

**Structural answer:** the continuity file has one invariant — always readable, or absent. Write
it atomically. A file that exists but does not parse is an error to raise, never a reason to
start over, because silently restarting is how an agent redoes finished work.

---

## 4 · The fifth one: no progress

Not in the source above. It came out of running
[harness-agent](../../examples/harness-agent/README.md) rather than reading it.

The harness retried a permanently-failing check until its session budget was exhausted, then
raised an error naming the budget. Three faults compounding:

1. Every remaining session was spent on the one thing that could not succeed.
2. The reported cause was the symptom. "Out of sessions" sends someone to raise the session
   limit, which does nothing.
3. The run threw away partial results it already had rather than returning them.

The bounded-loop rule this repository states in four places is *steps, wall-clock, tokens, and
no-progress*. The first three were implemented. The fourth was not, and the omission is not
visible by reading — each individual retry is correct behaviour.

**Structural answer:** a per-unit attempt cap, an `exhausted()` that names what never verified,
and a reset that is explicit. A harness that silently clears its own no-progress counter does
not have one.

The general lesson generalises past this example: **bounds you have not exercised are bounds
you have not got.** The step budget here was tested from the start because it was easy to test.
The no-progress bound was absent entirely, and no amount of review found it.

---

## 5 · What to write down

The continuity file is the whole of the agent's memory across windows, so its contents are a
design decision rather than a logging convenience.

| Include | Why |
| --- | --- |
| The feature or task list | Completion is evaluated against it |
| Per-item state | Distinguishes "not started" from "started and failing" |
| A session counter | Makes "how many attempts has this taken" answerable |
| A schema version | Lets the format change without silent misreads |

| Leave out | Why |
| --- | --- |
| The model's narrative summary | Unverifiable, and grows without bound |
| Full message history | That is the context window's job, not the continuity file's |
| Anything the environment already knows | Git history is better at being git history |

The last row is the useful one. A progress file that duplicates what `git log` already records
has two sources of truth that will disagree.

---

## 6 · Checklist

- [ ] There is an explicit list of units of work, written before the agent starts
- [ ] Completion is computed from recorded state, not asserted by the model
- [ ] Evidence is produced by something the model cannot edit
- [ ] A unit with no verification defined fails rather than passes
- [ ] One unit of work per context window, enforced in code
- [ ] The continuity file is written atomically
- [ ] A corrupt continuity file raises rather than restarting
- [ ] Every bound is exercised by a test, including no-progress
- [ ] Failures name the check that failed, not the budget that ran out

---

## Related

- [harness-agent](../../examples/harness-agent/README.md) — all of the above, in four modules with tests
- [Context engineering](CONTEXT-ENGINEERING.md) — the other half of harness work
- [Building blocks §4](BUILDING-BLOCKS.md) — orchestration and bounded loops
- [Building blocks §6](BUILDING-BLOCKS.md) — approval gates, the authorization counterpart to completion
- [Architecture patterns](ARCHITECTURE-PATTERNS.md) — autonomous loops and how to bound them
- [References](REFERENCES.md) — sourcing for the claims above
