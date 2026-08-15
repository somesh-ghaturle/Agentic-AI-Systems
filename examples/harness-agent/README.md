# harness-agent

A harness for an agent whose work outlives its context window — and the four things it refuses
to let that agent do.

```bash
python3 agent.py                                      # the demo, end to end
python3 -m unittest tests.test_harness_agent -v       # from the repository root
```

No dependencies, no model, no key.

## The problem

A long-running agent does not keep its working memory. The session ends, the context is gone,
and the next session starts from whatever was written down. Everything hard about that is a
consequence of one fact: **the agent is not a reliable narrator of its own progress.**

Ask a model whether the work is done and it will answer. The answer is a claim, and a harness
that accepts it has no verification step — it has a politeness ritual. So the four rules here
are all variations on moving a decision out of the model's reach:

| Rule | What it prevents |
| --- | --- |
| `finish()` consults the progress file | The agent declaring victory early |
| One `claim()` per session | Starting four features and finishing none |
| `COMPLETE` unreachable from `CLAIMED` | "Done" without evidence |
| Atomic writes to the progress file | A corrupt file the next session cannot read |

These are the failure modes named in Anthropic's
[Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents).
The mapping from each to the code that closes it is in [architecture.md](architecture.md).

## Layout

```text
harness/
├── state.py     the progress file, and the transitions it will accept
├── session.py   one context window, one feature, a step budget
├── verify.py    evidence the agent does not produce and cannot edit
└── runner.py    sessions in sequence, persisted between them
```

Read `state.py` first — everything else is arranged around the guarantee it makes: the file on
disk is always valid JSON matching the schema, or it does not exist. There is no third state.

## The bug the demo found

The first version retried a permanently-failing check until its session budget ran out, then
raised an error about the budget. Three things wrong at once: every remaining session wasted on
the one thing that could not succeed, a symptom reported instead of a cause, and `run()`
throwing away the partial results it already had.

The fix is a per-feature retry cap — the *no-progress* bound that
[BUILDING-BLOCKS §4](../../docs/agentic-system-architecture/BUILDING-BLOCKS.md) lists alongside
steps, wall-clock, and tokens. The first three were in the code from the start; the fourth was
missing, and reading the source had not shown it. Running it did.

Clearing the counter is deliberately manual (`reset_attempts`). A harness that silently resets
its own no-progress counter does not have one.

## Tests

36 tests, one class per failure mode, and **mutation-tested rather than trusted** — the same
standard as [hermes-agent](../hermes-agent/README.md). Nine deliberate breaks were introduced
into the invariants; every one of them turned the suite red:

| Mutation | Caught by |
| --- | --- |
| `advance` permits skipping states | `test_states_cannot_be_skipped` |
| `save` truncates before serializing | `test_a_failed_write_leaves_the_previous_version_intact` |
| `save` never renames its temp file | `test_no_temp_files_are_left_behind_after_a_failed_write` |
| `claim` allows a second feature | `test_a_second_claim_in_one_session_raises` |
| Step budget never trips | `test_the_step_budget_is_a_bound_not_a_suggestion` |
| `verify` advances on failure | `test_a_failing_verifier_leaves_the_feature_claimed` |
| `finish` stops checking | `test_finish_refuses_on_a_fresh_harness` |
| Retry cap removed | `test_exhausted_names_the_stuck_feature` |
| A missing check counts as a pass | `test_a_feature_with_no_verification_command_fails` |

That last one is worth stating on its own: a feature with no verification command **fails**.
Treating "no check defined" as a pass means adding a feature and forgetting its test marks it
complete, which is the failure mode arriving through the front door.

## Related

- [harness engineering](../../docs/agentic-system-architecture/HARNESS-ENGINEERING.md) — the concept
- [context engineering](../../docs/agentic-system-architecture/CONTEXT-ENGINEERING.md) — the other half of harness work
- [hermes-agent](../hermes-agent/README.md) — whether an agent is *allowed* to act, rather than whether it is finished
- [trace-eval](../trace-eval/README.md) — scoring the path rather than the answer
