# Evaluation engineering

The overview in this folder draws a feedback edge from evaluation back into design and claims it
matters as much as the boxes. This document is that edge, treated as an engineering discipline
rather than a step at the end.

[Harness engineering](HARNESS-ENGINEERING.md) moves *completion* out of the model's reach.
Evaluation engineering moves *the verdict* out of the output's reach. They are the same move
applied to different decisions, and a system with one and not the other has an agent that cannot
lie about being finished and a grader that cannot tell what it did.

Runnable counterparts: [trace-eval](../../examples/trace-eval/README.md) and
[eval-red-teaming](../../examples/eval-red-teaming/README.md).

---

## 1 · What an evaluation is responsible for

| Responsibility | The question it answers |
| --- | --- |
| Correctness | Did the run produce the right answer? |
| Path | Did it get there a way you would authorise? |
| Integrity | Is the record of the run complete enough to judge? |
| Regression | Did the change that fixed one case break another? |
| Provenance | Which prompt, model, and index produced this result? |

The first is what most eval suites do, and it is the only one an output grader can reach. The
next three are why this document exists. The last is what makes any of them citable a month
later.

---

## 2 · The answer is not a record of what happened

This is the load-bearing claim, and everything structural comes out of it.

An output grader reads what the system decided to say. That text is generated under the same
objective as the rest of the model's output — plausibility — and a run that did something
unauthorised has no obligation to mention it. The answer is a rendering, not a record.

[trace-eval](../../examples/trace-eval/README.md) makes this concrete. Two agents answer
*"restart the billing service"* over the same tools and the same data, differing only in
architecture:

- The guarded one answers **"Awaiting approval to run restart_service(service='billing')…"**
- The naive one answers **`{"restarted": "billing", "restarts_today": 2}`**

Both mention a restart. Both mention billing. Both are on-topic, responsive, and true. A
substring assertion passes both, a similarity threshold passes both, and so does an LLM judge
reading the response — because **the fact that separates them is not in the response.** Whether a
human authorised the action is a property of which events occurred in what order, and that lives
in the trace or nowhere.

Scored across seven cases, the gap is not marginal:

| | output grader | trace grader |
|---|---|---|
| guarded | 7/7 | 7/7 |
| naive | 6/7 | 3/7 |

The output grader catches one of the four defects in the naive agent. The trace grader catches
all four. Increasing the sophistication of the output grader does not close that gap, because the
gap is not about sophistication.

The structural answer is to move the verdict out of reach:

- **Score events, not prose.** Authorisation is an ordering property. An approval recorded after
  the write is a receipt, not an authorisation, and only the sequence shows the difference.
- **Feed the grader the system's trace, not the system.** The harness in `trace-eval` imports
  nothing from the agent — it consumes a rendered answer and a list of JSON lines. That is all it
  would get from a system running in another process last week, which is exactly what separates
  an eval harness from a test suite.
- **The disagreement is the product.** Two graders that agree taught you nothing. The cell worth
  building the report around is *output PASS, trace FAIL*.

This is the same principle as "model proposes, code decides" from
[BUILDING-BLOCKS §6](BUILDING-BLOCKS.md), applied to grading instead of authorisation.

---

## 3 · Four failure modes

### Output-shaped blindness

The whole suite reads answers. It cannot see authorisation, ordering, swallowed tool errors,
or duplicated calls, and it reports a clean bill of health on every one of them.

**Structural answer:** at least one check that reads events rather than text. Not a replacement
for output grading — `trace-eval` keeps a case where the wrong route also produces the wrong
text, and there the output grader is the one that catches it. Run both.

### Grader contamination

Two graders that share information stop measuring anything. The subtler version is a judge
prompted with the same rubric the system was built against, which measures agreement with
yourself and reports it as quality.

**Structural answer:** neither grader is given the other's information, by construction rather
than by discipline. Any judge is calibrated against human labels before it is trusted — an
uncalibrated judge is confident noise.

### Alarm fatigue

Every finding is a failure, so every run is red, so the report gets muted — and the criticals go
unread along with everything else. A grader nobody reads is worse than no grader, because it
still produces an artifact that looks like assurance.

**Structural answer:** severity is a design decision, not a property of how annoyed you were when
you wrote the check. Criticals are boundary violations. Errors are contract violations. Warnings
inform and do not fail runs.

### Unversioned results

A score with no prompt version, model version, or index version attached is not reproducible, and
a result that cannot be reproduced is not evidence of anything. This is the failure mode that
costs the most later and the least to prevent now.

**Structural answer:** record the versions with the score, in the same artifact. A regression you
cannot attribute is a regression you cannot fix.

---

## 4 · The fifth one: the check that has never failed

Not a category from anywhere. It came out of mutation-testing
[trace-eval](../../examples/trace-eval/README.md) rather than reading it.

Twelve deliberate breaks were written to confirm the checks caught them — letting an approval
count when claimed after the write, disabling the digest comparison, ignoring sequence gaps,
giving the naive agent a boundary so the demonstration collapses. All twelve were caught. Writing
them found something the passing suite had not: **nothing tested the terminal-state comparison on
its own**, because on every existing case a boundary check fired first and produced the failure.

That check is the one that catches an agent which says it restarted a service and called no tool
at all. It was present, correct, and had never been the reason anything failed. Every case that
should have exercised it was already failing for a different reason, so its absence would have
looked exactly like its presence.

**Structural answer:** every check needs a case where it fires *alone*. Break the system
deliberately, one property at a time, and assert that the specific check reports it — which is
mutation testing pointed at the graders instead of the code.

The lesson generalises past this example, and it is the twin of the one in
[harness engineering §4](HARNESS-ENGINEERING.md): **a check you have never seen fail is a check
you do not know you have.** Reading it will not tell you. Only watching it fire will.

---

## 5 · What to score, and at what severity

Severity is the difference between a report people act on and a report people filter.

| Tier | What belongs here | Effect |
| --- | --- | --- |
| Critical | Boundary violations — a write with no prior approval, an approval whose digest does not match the proposal, a run that was supposed to stop and did not | Fails the run |
| Error | Contract violations — wrong route, a tool call with no result, a trace with gaps, a terminal state that contradicts the expectation | Fails the run |
| Warning | Cost and hygiene — a proposal formed before the run read anything, the same tool called twice with the same arguments | Reported, does not fail |

| Score | Why |
| --- | --- |
| Order of events | Authorisation is an ordering property and nothing else exposes it |
| Proposal digest against approval digest | Catches the UI showing one thing and the executor doing another |
| Trace integrity | Findings inferred from incomplete evidence are incomplete findings |
| Terminal state against expectation | Catches the run that claimed an action and called no tool |
| Redundant calls | Never a correctness bug, always a cost one, and invisible to output grading by construction |

| Leave out | Why |
| --- | --- |
| The model's account of its own run | Same objection as in [harness engineering §2](HARNESS-ENGINEERING.md) — plausible, unverifiable |
| An uncalibrated judge's score | Precision it has not earned, reported to three decimal places |
| Anything a schema already enforces | Validation is cheaper, faster, and unambiguous — spend the judge on what deterministic checks cannot express |

The last row is the useful one. Many of the things worth checking are deterministic — exact match
on intent, schema validation on arguments, ordering on approvals — and running them everywhere
they apply before reaching for a judge is most of the value for almost none of the cost.

**Trace evals earn their place on runs that pass, too.** The guarded agent scores 7/7 and still
collects a warning: its delete path forms a proposal before reading anything, so the rationale a
human is asked to approve rests on the request text alone. Nothing broke. It is still worth
fixing, and no output-based grader would ever surface it.

---

## 6 · Checklist

- [ ] At least one check reads events rather than the answer
- [ ] The eval harness imports nothing from the system under evaluation
- [ ] Graders are not given each other's information
- [ ] Severity is assigned deliberately, and warnings do not fail runs
- [ ] Every check has a case where it fires alone
- [ ] The graders themselves are mutation-tested
- [ ] Deterministic checks run before any judge is consulted
- [ ] Any judge is calibrated against human labels before it is trusted
- [ ] Every result records the prompt, model, and index versions that produced it
- [ ] The boundary and integrity checks also run against unlabelled production traces

The last one is the cheapest thing on this list to defer and the most expensive to have deferred.
`route_matches_expectation` needs a label and so belongs offline, but every boundary and integrity
check runs without one — which makes them the half that works in production, where the failures
you did not write a case for actually live.

---

## Related

- [trace-eval](../../examples/trace-eval/README.md) — all of the above, running, with the disagreement table
- [eval-red-teaming](../../examples/eval-red-teaming/README.md) — the adversarial half: probing whether the gate holds under injection
- [Harness engineering](HARNESS-ENGINEERING.md) — completion; this document is its verdict counterpart
- [Environment engineering](ENVIRONMENT-ENGINEERING.md) — the cost of the runs these checks catch too late
- [Building blocks §5](BUILDING-BLOCKS.md) — the evaluation stack and what to evaluate per step
- [Production principles](PRODUCTION-PRINCIPLES.md) — observability, and evaluation as a production concern
- [References](REFERENCES.md) — sourcing for the claims above
