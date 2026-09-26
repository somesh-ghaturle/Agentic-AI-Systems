# budget-guard

A bounded autonomous loop where the agent chooses its own next step, bounded by a per-request token budget.

The architecture docs name four bounds an autonomous loop needs: steps, wall-clock, tokens, and no-progress. The [harness-agent](../harness-agent/README.md) exercises three. This example exercises the one that is left: a per-request token budget.

A step budget fires after a fixed count. A token budget fires *before* a spend that would exceed what remains. The difference matters: a step-count limit lets the agent start a step it cannot finish, a token budget does not, because the check is before the spend, not after. The agent that spent its last tokens on a step that could not complete is the failure mode this example exists to make visible.

## What it demonstrates

- **The autonomous loop pattern** from [ARCHITECTURE-PATTERNS.md](../../docs/agentic-system-architecture/ARCHITECTURE-PATTERNS.md). The agent decides its own next step -- it refines if review found a gap -- rather than following a fixed pipeline.
- **The token budget bound** from [PRODUCTION-PRINCIPLES.md](../../docs/agentic-system-architecture/PRODUCTION-PRINCIPLES.md): "Enforce strict token limits."
- **Graceful degradation.** When budget is tight, the agent takes a cheaper ("quick") version of the same step, so it degrades rather than hard-stopping with half an answer.
- **Naming what was lost.** When even the quick version does not fit, the agent stops and names what it completed and what it skipped. "Skipped: review" tells you the answer is unreviewed; "budget exhausted" tells you nothing.

## Run

```bash
python3 examples/budget-guard/agent.py "summarize the refund policy"
python3 examples/budget-guard/agent.py "summarize the refund policy" --budget 1500
python3 examples/budget-guard/agent.py "summarize the refund policy" --budget 500
```

The first command gives the agent enough budget to run every step thoroughly. The second forces it into quick mode for the later steps. The third exhausts the budget before the agent finishes, so you see what it names as skipped.

## What this is not

Not token accounting. Every step's cost is a constant in `THOROUGH_COST` and `QUICK_COST`, known
before the step runs. A real model call's cost is known only afterwards -- output length is the
model's choice -- so "check before the spend" needs a reservation: cap each call's `max_tokens`
at what remains and treat that cap as the spend. Without it, the last call can still overrun.

The loop also never truly loops back. `_do_analyze` resets `_gathered` only when nothing was
gathered, and `_do_gather` never gathers nothing, so the gather-again branch the docstring
describes is unreachable as written. The budget logic is what this example tests; the
autonomy around it is scaffolding.

## Security

This example makes no security claim. It reads from a simulated knowledge base, produces text, and prints. It has no approval flow, no write boundary, and no network access. It would be inadequate as a production service, which is documented here rather than discovered later.

## See also

- [harness-agent](../harness-agent/README.md) -- the other three bounds (steps, wall-clock, no-progress)
- [PRODUCTION-PRINCIPLES.md](../../docs/agentic-system-architecture/PRODUCTION-PRINCIPLES.md) -- "Enforce strict token limits"
- [ARCHITECTURE-PATTERNS.md](../../docs/agentic-system-architecture/ARCHITECTURE-PATTERNS.md) -- the autonomous loop pattern
- [HARNESS-ENGINEERING.md](../../docs/agentic-system-architecture/HARNESS-ENGINEERING.md) -- "bounds you have not exercised are bounds you have not got"
- [ENVIRONMENT-ENGINEERING.md](../../docs/agentic-system-architecture/ENVIRONMENT-ENGINEERING.md) -- the chapter that names this a runnable counterpart: a cap checked before the spend rather than after
