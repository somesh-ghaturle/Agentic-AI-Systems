# context-overflow

The point at which a long conversation stops being useful, before the model has hit its formal
limit. The example shows why the naive fix — keep the most recent N messages — is usually the
wrong one.

```bash
python3 overflow.py
```

No dependencies, no model, no key.

## The idea

A model's context degrades before it is full. The weaker signal is not a crash; it is the moment
where a long, recent tail of tool output outweighs the oldest decision that now constrains every
future turn. That is an overflow even when the API has not started erroring.

This example models a real-ish migration conversation: the system prompt, the design decision, and
an unresolved question are all old; the recent turns are all `test run:` and `Reading ...` noise.
The naive strategy keeps the noise and drops the decision.

## The failure mode

The bug is not that the token budget is wrong. It is that the retention policy is the wrong one:

- recency and relevance are different axes
- the oldest decision is often the thing that matters most
- the recent tool chatter is cheap and soon obsolete

The code compares two strategies:

1. `truncate_by_recency()` — keep the newest messages until the budget is reached
2. `keep_critical_messages()` — always keep the system prompt and the decisions, then spend the
   remaining budget on the most relevant recent context

## What is simplified

This is not a tokeniser or a production context manager. It models the failure mode with a rough
word count and a small toy conversation. That is enough to make the design point legible: context
budgeting is not a queue problem, it is a relevance problem.

## Related

- [context-compaction](../context-compaction/README.md) — the policy that preserves decisions and
  drops resolved detail instead of keeping the recent tail
- [CONTEXT-ENGINEERING.md](../../docs/agentic-system-architecture/CONTEXT-ENGINEERING.md) — the
  broader treatment of finite windows and degradation before the limit

## Security

This example makes no security claim. It demonstrates context budgeting and the degradation that
happens before the model reaches an API error; it does not enforce a write boundary or a policy
decision.
