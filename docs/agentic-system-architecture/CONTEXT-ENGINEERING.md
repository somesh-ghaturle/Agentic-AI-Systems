# Context engineering

Context engineering is deciding what the model sees. Prompt engineering was a subset of it —
the instructions — back when the instructions were most of what there was. In an agentic system
they are a minority of the tokens, outnumbered by tool definitions, retrieved documents, and a
message history that grows every turn.

The reframing is the useful part: the question stops being *what wording works* and becomes
*what configuration of context makes the desired behaviour likely*.

Primary source: [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents).
Runnable counterpart: [context-compaction](../../examples/context-compaction/README.md).

---

## 1 · Context is finite, and degrades before it is full

The naive model of a context window is a bucket: it works until it overflows. The real
behaviour is worse, because quality falls off well before the limit.

**Context rot** is the name for that degradation. The mechanism is attention: every token
attends to every other, so relationships scale as n², and a model's training distribution
contains far more short sequences than long ones. Long contexts are both computationally
strained and comparatively unfamiliar.

Two consequences that change how you build:

- **More context is not free, even when it fits.** Padding a prompt with everything possibly
  relevant has a cost paid in attention over the things that actually were.
- **"It fits in the window" is not a design.** The budget worth managing is the one where
  performance holds, not the one where the API stops erroring.

This is the same argument as the token-budget line in
[PRODUCTION-PRINCIPLES.md](PRODUCTION-PRINCIPLES.md), stated from the quality side rather than
the cost side.

---

## 2 · Four strategies for long-horizon work

### Compaction

Summarize the history, keep what still constrains the future, restart with the compressed
version plus recent detail.

What survives compaction is the design decision. Architectural decisions and unresolved
questions must; resolved detail and superseded attempts must not. A compaction that keeps the
most recent N messages is not compaction, it is truncation with extra steps — recency and
relevance are different axes, and the decision that shapes everything is usually old.

The [context-compaction](../../examples/context-compaction/README.md) example implements this
distinction explicitly and shows the before/after token counts.

### Structured note-taking

The agent maintains an external file — progress notes, decisions, open questions — that outlives
the window. Cheap, and it converts "remember this" from a context problem into a filesystem
problem.

The discipline is the same as the continuity file in [harness engineering](HARNESS-ENGINEERING.md):
write what cannot be recovered from the environment, and nothing that can. Notes duplicating
`git log` create a second source of truth that will drift.

### Sub-agent architectures

A focused task runs in its own clean window and returns a distilled result to a coordinator. The
coordinator's context grows by a summary rather than by a full transcript.

The cost is real and is covered in [ARCHITECTURE-PATTERNS.md](ARCHITECTURE-PATTERNS.md):
coordination overhead, more failure modes, harder debugging. Decompose on evidence that a single
agent's context is the binding constraint — not in anticipation of it.

### Just-in-time retrieval

Hold lightweight identifiers — paths, IDs, queries — and load contents only when needed, rather
than pre-loading everything that might matter.

This is why a file path is often a better thing to put in context than a file. The agent that
can list a directory and read on demand has the whole tree available at the cost of a few
tokens, and reads the three files that matter instead of the forty that might.

---

## 3 · System prompt altitude

Both extremes fail, and they fail in ways that look like opposites:

| Too low | Too high |
| --- | --- |
| Hardcoded if-this-then-that for every case | "Be helpful and use good judgment" |
| Brittle — breaks on the case not enumerated | Vague — assumes context the model does not have |
| Grows without bound as cases accumulate | Stays short and stops determining behaviour |

The target is strong heuristics: specific enough to guide, general enough to transfer. Structure
the prompt into distinct sections with headers or XML tags, because retrieval within a prompt is
a real effect and an unstructured wall is harder to attend over.

A practical test: if a new edge case requires a new rule, altitude is too low. If two engineers
read the prompt and predict different behaviour, it is too high.

---

## 4 · Tools and examples are context too

Tool definitions occupy the window on every turn, which makes tool design a context decision as
much as an API one.

- **Self-contained, robust to error, unambiguous about when to use them.** See
  [BUILDING-BLOCKS §2](BUILDING-BLOCKS.md) for the contract side.
- **No overlapping functionality.** Two tools that could each plausibly serve a request create a
  decision point with no correct answer, and the model will sometimes get it wrong — not because
  it is weak, but because the question was underdetermined.
- **Curate examples, do not enumerate them.** A few diverse canonical cases communicate the shape
  of the task. An exhaustive list of edge cases is a large token cost that teaches the pattern
  less well.

---

## 5 · Checklist

- [ ] The context budget is set by where quality holds, not by the model's maximum
- [ ] Something bounds context growth per request — compaction, or a hard cap
- [ ] Compaction preserves decisions and open questions, not merely recent messages
- [ ] Notes hold what the environment cannot already tell you, and nothing else
- [ ] Retrieval is just-in-time where the corpus is larger than the window
- [ ] Sub-agents were introduced on evidence, not in anticipation
- [ ] The system prompt is sectioned, and neither a rulebook nor a platitude
- [ ] No two tools plausibly answer the same request
- [ ] Examples are canonical and few

---

## Related

- [context-compaction](../../examples/context-compaction/README.md) — decisions kept, resolved detail dropped
- [Harness engineering](HARNESS-ENGINEERING.md) — the loop and continuity side
- [Building blocks §3](BUILDING-BLOCKS.md) — memory and state
- [Production principles](PRODUCTION-PRINCIPLES.md) — context and RAG design, token budgets
- [References](REFERENCES.md) — sourcing
