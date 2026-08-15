# context-compaction

Compaction that keeps decisions and drops resolved detail — and the contrast with truncation,
which is the implementation everyone writes first.

```bash
python3 compact.py
```

No dependencies, no model, no key.

## The idea

When a conversation outgrows its budget, something has to go. The obvious rule is *keep the
most recent N messages*, and it is wrong in a specific way:

**Recency and relevance are different axes.** The decision that constrains every future turn is
usually the oldest thing in the history. Truncation reliably discards it while keeping the tool
output from thirty seconds ago.

The example runs a real-ish migration conversation through both and prints the difference. The
architectural decision — single-table design, the partition and sort keys — survives compaction
and is lost to truncation, which instead keeps three test-run lines and two directory listings.

## The policy

Three categories, checked in order:

| Class | What lands here | Fate |
| --- | --- | --- |
| `keep` | The system message; decisions; open questions; schema and index design | Verbatim |
| `drop` | Tool results, progress chatter (`Reading ...`, `test run:`) | Gone |
| `summarize` | Everything else — exploratory reasoning that reached a conclusion | One line saying how much was omitted |

Plus a small allowance: the last couple of messages survive regardless of class, because an
agent resuming mid-thought needs to know what it just did. That is a concession to continuity
on top of the policy, not the policy itself.

## The bug running it found

The first version classified the system message as ordinary prose and folded it into the summary
line. The compacted history came back with no instructions in it at all.

That is compaction defeating its own purpose — the context existed to serve the system prompt,
and the compactor threw the system prompt away to make room for context. The fix is one branch
checked before all others: `role == "system"` is always kept.

It is a good illustration of why this policy is worth seeing without a model attached. The
failure is completely obvious in the printed output and completely invisible in a design
discussion.

**16 tests pin the policy now**, four of them on this specific bug. Deleting the one-line guard
turns all four red.

## What is simplified

The classifier is keyword-based (`DECISION:`, `OPEN QUESTION:`, `PK=`, `GSI`). A real system
would use a model to classify, or — better — have the agent tag messages as it produces them,
which turns a recall problem into a bookkeeping one.

The token count is `len(re.findall(r"\S+", text))`, a whitespace word count. It shows a ratio
honestly; it is not a tokenizer and does not claim to be.

Neither simplification touches the subject. The retention policy is the thing worth arguing
with, and it is legible here in about thirty lines.

## Related

- [Context engineering](../../docs/agentic-system-architecture/CONTEXT-ENGINEERING.md) — the concept, and the other three strategies
- [Harness engineering](../../docs/agentic-system-architecture/HARNESS-ENGINEERING.md) — what survives *between* windows, rather than within one
- [harness-agent](../harness-agent/README.md) — the worked example of that
- [Building blocks §3](../../docs/agentic-system-architecture/BUILDING-BLOCKS.md) — memory and state
