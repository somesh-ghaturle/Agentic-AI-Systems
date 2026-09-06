# Environment engineering

The other chapters in this folder are about constraining the agent. [Context](CONTEXT-ENGINEERING.md)
governs what it sees, [harness](HARNESS-ENGINEERING.md) governs what it may conclude, and
[evaluation](EVALUATION-ENGINEERING.md) governs how you find out whether any of it worked.

This one is about the world it acts in — and it starts from the assumption the others are
allowed to make and this one is not: **that the controls fire.**

You cannot build an agent that never takes a wrong action. You can build a world where a wrong
action is cheap, visible, and reversible. Those are properties of the environment, not of the
model, and they are decided before the agent ever runs.

Runnable counterparts: [budget-guard](../../examples/budget-guard/README.md),
[checkpoint-agent](../../examples/checkpoint-agent/README.md),
[approval-gate-fuzzing](../../examples/approval-gate-fuzzing/README.md), and the four
[infra/](../../infra/) trees.

---

## 1 · What the environment is responsible for

| Responsibility | The question it answers |
| --- | --- |
| Blast radius | If this action is wrong, how much is wrong? |
| Reversibility | Can it be undone, and should it be? |
| Recoverability | Is there a path back, and does it exist yet? |
| Replay safety | What happens if this runs twice? |
| Fidelity | Does the environment you test in behave like the one you ship to? |

None of these are answered by a better prompt, a stricter gate, or a smarter model. They are
answered by infrastructure decisions that are expensive to revisit, which is why they belong
before the build rather than after the incident.

---

## 2 · Every control is enforced only where it is enforced

This is the load-bearing claim, and it is less obvious than it sounds.

A boundary described in a design document is enforced in the specific places someone wrote code
for. If it holds in one of two paths, it holds in one — and the document, the diagram, and the
review will all keep describing it as a boundary.

This repository has its own instance of that, recorded in the comment at the top of the AWS
write-boundary test. The stated claim was that the AWS tree needed no such test, because the
boundary is a Lambda resource policy and getting it wrong is a plan-time error:

> That is true of the resource policy and only of the resource policy. […] For a caller in the
> SAME ACCOUNT, Lambda grants invocation if the identity policy allows it **or** the resource
> policy does.

The orchestrator's identity policy is built from a variable, and nothing checked what went into
it. Substituting `tool_arns_by_name` for `read_tool_arns` — a one-word edit that reads as a
simplification — lets the state machine invoke the write tools directly. No precondition fires,
`terraform validate` passes, and the plan shows an IAM statement quietly gaining an ARN.

The lesson is not "AWS IAM is confusing". It is that **a control with two enforcement points and
one test has one enforcement point**, and that the untested half will be the one that reads as
harmless in review. Prevention is not a thing you have; it is a thing you have *at specific
coordinates*, and the environment is what decides the cost everywhere else.

The structural answer:

- **Enumerate the paths to the effect, not the paths through your code.** The question is not
  "where do we call the write tool" but "what could invoke it".
- **Assume one control fails and price the result.** If the answer is unbounded, the missing work
  is environmental, not procedural.
- **Test the boundary from the outside.** The AWS suite reads the source rather than a plan, so it
  needs no credentials and runs anywhere — a boundary test that only runs where secrets exist is a
  boundary test that does not run.

---

## 3 · Four properties to design deliberately

### Reversibility, and which direction it should fail in

The instinct is to make everything undoable. That is wrong, and this repository contains the
counterexample.

Every tree's `modules/archive` is built the opposite way on purpose — S3 Object Lock, an Azure
immutability policy, GCP Bucket Lock — off by default and, once on, irreversible by design.
[HOW-TO-RECOVER.md](../HOW-TO-RECOVER.md) says why:

> The point isn't convenience recovery; it's that nobody, including an administrator, can quietly
> repair or erase an entry once the lock is on. **Evidence that can be fixed after the fact stops
> being evidence.**

So reversibility is not a good to maximise. It is a per-resource decision with a direction:
operational state should fail toward *recoverable*, and audit evidence should fail toward
*immutable*. Getting the direction backwards is how you end up with a system where the refund can
never be undone and the log of who approved it can.

**Decide the direction for each store before building, and write it down.** A reader who cannot
tell which way a resource is supposed to fail cannot review a change to it.

### Blast radius

Scope is the cheapest control in this chapter, and the one most often left at its default.
Credentials scoped to the tools actually called, namespaces the agent cannot escape, tenancy that
holds without the agent cooperating, and hard caps on spend and rate.

[budget-guard](../../examples/budget-guard/README.md) makes the sharp version of the caps
argument. A step budget and a token budget sound interchangeable and are not:

> A step budget fires after a fixed count. A token budget fires *before* a spend that would
> exceed what remains. […] a step-count limit lets the agent start a step it cannot finish, a
> token budget does not, because the check is before the spend, not after.

That distinction generalises past tokens. A cap checked after the effect is an alarm; a cap
checked before it is a control. Both are worth having and only one of them bounds anything.

### Recoverability

A recovery path that does not exist yet does not exist. This is the property that is always
cheap in advance and never cheap afterwards, and the repository is candid about being on the
wrong side of it:

> All four trees apply against a **local** Terraform state file today. […] The only copy of
> Terraform's own state lives on whichever machine last ran `apply`. […] Uncommenting the backend
> block for your environment before that happens is cheaper than reconstructing state after.

Note the shape of that: the backend blocks are *written out and commented*. The recovery path is
one edit away and has not been taken, which is more honest than most systems manage and still
means the path is not there. **Write the runbook before the incident, then confirm the steps in
it can actually be run** — an untried runbook is a document about recovery, not a recovery.

### Replay safety

Anything that can crash mid-action can run that action twice, and an agent that resumes is an
agent that replays. [checkpoint-agent](../../examples/checkpoint-agent/README.md) carries the
three rules: atomic writes so a crash mid-write cannot corrupt the file, checkpoints after every
action so little is lost, and a plain diffable format so a human can read yesterday's state.

The property that matters most is the one its tests assert directly — *replaying an action does
not repeat the work*. Idempotency is what makes retry safe, and retry is what every other bound
in this repository assumes is available.

---

## 4 · The fifth one: the environment you test in is not the environment you ship to

Not a category from anywhere. It comes from a decision this repository made deliberately and
recorded as a decision: CI runs `terraform validate`, never `terraform plan`, because `plan`
needs cloud credentials and the no-secrets constraint on CI is worth more than the extra
coverage.

That is the right trade. It is also, precisely, a fidelity gap — and the AWS write-boundary test
exists *because* of it. `validate` passes while the identity policy is wide open. The check that
catches it had to be written separately, against the source, because the environment CI can
reach does not contain the failure.

The general form: **every sandbox differs from production somewhere, and the difference is where
your evidence stops.** A dry-run that does not exercise IAM tells you nothing about IAM. A
simulator with no rate limits will never show you the behaviour under one. A test account with
one tenant cannot demonstrate isolation.

**Structural answer:** name the gap rather than close it dishonestly. State what the sandbox does
not model, and write a separate check for each thing on that list — the way the AWS suite reads
Terraform source rather than pretending `validate` covered it. A sandbox whose divergences are
written down is a useful instrument. One whose divergences are assumed away is a source of
confident wrong answers, which is the same failure this repository keeps finding everywhere else:
a check that looks authoritative and verifies nothing.

---

## 5 · What to decide before building

| Decide | Why it has to be early |
| --- | --- |
| Which direction each store fails in | Retrofitting immutability onto a mutable log destroys the evidence you wanted |
| The credential scope per tool | Widening is a one-line edit; narrowing after integration is a migration |
| Hard caps, and whether each is checked before or after the effect | An after-the-fact cap cannot be upgraded into a control without moving the check |
| Where state lives and how it is restored | The cheapest moment is before there is state worth losing |
| What the sandbox does not model | The list stops being writable once people trust the sandbox |

| Do not rely on | Why |
| --- | --- |
| The agent declining to do the harmful thing | Same objection as [harness §2](HARNESS-ENGINEERING.md) — plausible, unverifiable, and not a control |
| A gate you have never seen refuse | [Evaluation §4](EVALUATION-ENGINEERING.md) — a check you have not watched fire is one you do not know you have. [approval-gate-fuzzing](../../examples/approval-gate-fuzzing/README.md) is that check, run against bypass phrasing |
| A boundary enforced in one of two paths | §2 above; the untested path is the one that reads as harmless |
| A runbook nobody has executed | Recovery you have not rehearsed is recovery you are guessing at |

---

## 6 · Checklist

- [ ] Every path that can reach a write effect is enumerated, not just the intended one
- [ ] Each boundary has a test that runs without credentials
- [ ] Each store has a documented direction it fails in — recoverable or immutable
- [ ] Credentials are scoped to the tools actually called, not the tools that exist
- [ ] Every cap states whether it is checked before or after the effect
- [ ] Actions that can be retried are idempotent, and a test asserts it
- [ ] State writes are atomic, and a corrupt file raises rather than resetting
- [ ] The recovery path exists now, and someone has run it end to end
- [ ] What the sandbox does not model is written down
- [ ] Each unmodelled thing has its own check, outside the sandbox

---

## Related

- [budget-guard](../../examples/budget-guard/README.md) — a cap checked before the spend rather than after
- [checkpoint-agent](../../examples/checkpoint-agent/README.md) — atomic writes, and replay that does not repeat work
- [approval-gate-fuzzing](../../examples/approval-gate-fuzzing/README.md) — watching the gate refuse, in many phrasings
- [infra/](../../infra/) — the write boundary enforced by cloud IAM rather than by application code
- [HOW-TO-RECOVER.md](../HOW-TO-RECOVER.md) — the operational counterpart to §3
- [THREAT-MODEL.md](../THREAT-MODEL.md) — what these controls defend against
- [Building blocks §6](BUILDING-BLOCKS.md) — approval gates, which decide *whether*; this chapter is about the cost when they do not
- [Harness engineering](HARNESS-ENGINEERING.md) · [Evaluation engineering](EVALUATION-ENGINEERING.md) — the other two halves of the same move
- [References](REFERENCES.md) — sourcing for the claims above
