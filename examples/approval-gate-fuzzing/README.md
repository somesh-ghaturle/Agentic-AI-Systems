# approval-gate-fuzzing

A tiny fuzz suite for the approval boundary: it scans a short list of bypass phrases and checks
whether a naive agent would comply with a prompt that tries to suppress or override the approval
step.

```bash
python3 fuzz.py
```

No dependencies, no model, no key.

## The idea

The problem is not only that a model can be instructed to do something unsafe. The more interesting
failure mode is that the model might decide the instruction is just a new rule and follow it even
when it conflicts with the approval gate.

This example stresses exactly that class of prompt: strings like "ignore the approval gate",
"skip human approval", and "system override" are turned into a small regression set. The harness
compares the naive path with a policy-aware guard and asks whether a would-be bypass would ever
reach a write.

## Why this matters

A single static prompt is too easy to reason about. A production system needs a set of variants that
keep surfacing the same core bug in different language: different wording, different urgency,
and different framing all try to get the model to treat approval as a suggestion instead of a
hard requirement.

A finite fuzz suite is not a substitute for a full adversarial eval, but it is a useful way to turn
security review into a repeatable check that can live in the repository.

## Related

- [eval-red-teaming](../eval-red-teaming/README.md) — the sharper prompt-injection case that uses
  the same approval boundary idea in a one-shot example
- [hermes-agent](../hermes-agent/README.md) — the application-level enforcement of the approval
  gate itself
- [THREAT-MODEL.md](../../docs/THREAT-MODEL.md) — the repo's write-boundary security model

## Security

This example does not execute real writes. It models a testing harness only: a malicious prompt is
recognized as a test case and blocked before any action is possible.

---

- [ENVIRONMENT-ENGINEERING.md](../../docs/agentic-system-architecture/ENVIRONMENT-ENGINEERING.md) -- the chapter that names this a runnable counterpart: a gate you have never watched refuse is one you do not know you have
