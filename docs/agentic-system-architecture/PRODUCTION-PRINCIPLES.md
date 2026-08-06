# Production engineering principles

What separates a demo that works from a system that keeps working. Everything here assumes
the building blocks are in place — this is about making them survive contact with real
traffic.

---

## Reliability

### Decompose large prompts into atomic steps

A single prompt asked to classify, retrieve, reason, and format produces failures you
cannot localize. When it goes wrong you know only that *something* did.

Atomic steps each have one job, one output contract, and one failure mode. You can test
them independently, evaluate them independently, and route them to different models. The
decomposition is what makes the rest of this document possible.

### Treat every LLM call as an untrusted dependency

Because it is one. It is a network call to a third party that can be slow, rate-limited,
temporarily degraded, or return something that does not match your schema.

Every call gets:

- **A timeout.** Always. A hung call with no timeout holds a worker until something else
  breaks
- **Retry with backoff** on rate limits and transient errors — with a cap, and with jitter
- **Schema validation on the response**, with a defined path when validation fails
- **A fallback** — retry, escalate to a different model, or fail cleanly with a useful
  error. Decide in advance

The mental model that helps: you would not call a payment gateway without a timeout and an
error path. This is the same, and it fails more often.

### Design the failure paths

For each step: what happens when the model returns malformed output, when the tool times
out, when retrieval returns nothing, when the user abandons mid-approval, when the process
restarts mid-workflow?

Systems fail on the paths nobody designed. In agentic systems those paths are unusually
numerous, because every step has a probabilistic component.

### Make everything resumable

State persisted outside the process, keyed by a correlation ID. A deploy mid-workflow
should not lose the workflow. This costs little at design time and is expensive to retrofit.

---

## Cost and latency

The two are usually improved by the same changes, which makes this the highest-leverage
optimization work.

### Model routing

Covered in [BUILDING-BLOCKS.md](BUILDING-BLOCKS.md#1--model-layer-and-routing). It is
listed first here too, because it is typically the largest single win available.

### Enforce strict token limits

Per step and per request. Unbounded context growth is the standard failure: a loop appends
tool output to context each iteration, and by iteration twelve you are paying for eleven
copies of things nobody needs.

Cap input tokens per call, cap total tokens per request, and truncate or summarize
deliberately rather than letting context grow by accident.

### Cache aggressively

- **RAG retrieval results.** Same query, same corpus, same answer.
- **Policy and config lookups.** Changes rarely, read constantly.
- **System prompts and few-shot examples.** Identical across requests — use prompt caching where the provider supports it.
- **Embeddings.** Deterministic for a given input and model.
- **Tool results for idempotent reads.** Reference data does not change per request.

Prompt caching deserves specific attention: it rewards putting the stable content
(instructions, examples, schemas) at the front and the variable content at the end. That is
a small structural change with a large cost effect.

### Stream user-facing output

Does not reduce total latency but transforms perceived latency. A response streaming at
two seconds feels faster than a complete response at four.

Do not stream intermediate reasoning steps to users. It looks impressive in a demo and
exposes internal state that is often wrong before it is right.

### Measure before optimizing

Log per-step cost and latency from day one. Optimization without measurement targets the
step you *think* is expensive, which is usually not the one that is.

---

## Context and RAG design

### Retrieval quality dominates

More context is not better context. A precise chunk beats ten loosely related ones —
irrelevant context does not merely waste tokens, it actively degrades reasoning by giving
the model plausible-looking material to latch onto.

The techniques, in the order they usually pay off:

- **Chunking strategy.** Chunks that split mid-thought retrieve badly. Chunk on semantic boundaries, overlap slightly.
- **Metadata filtering.** Restricting by tenant, date, document type, or permission *before* semantic search cuts the candidate set and prevents cross-tenant leakage.
- **Hybrid search.** Semantic search misses exact terms — error codes, product IDs, names. Combining with keyword search fixes a whole class of misses.
- **Re-ranking.** A cross-encoder over the top fifty candidates reliably beats raw vector similarity for final ordering.

### Separate instructions from untrusted content

**Architecturally important, not a formatting preference.**

Developer system instructions, user input, and retrieved documents must be clearly
delineated in the prompt. Retrieved documents and user content are **untrusted** — a
document in your corpus can contain text phrased as instructions, and the model has no
inherent way to distinguish that from your actual instructions.

This is prompt injection, and in a RAG system the attack surface is your entire corpus.
Anyone who can get a document into your index can attempt it.

Mitigations that work: explicit delimiters and role separation, instructions stating that
retrieved content is reference material only, output validation before any action, and —
most importantly — never letting retrieved content directly trigger a write. See
[AGENT-SECURITY.md](../agentic-coding-playbook/AGENT-SECURITY.md) for the full treatment.

### Evaluate retrieval separately

Retrieval quality is measurable on its own: recall@k, precision, human relevance labels.
Do that before evaluating end-to-end quality — most "the model gave a bad answer" failures
are actually "retrieval gave it bad material," and those have entirely different fixes.

---

## Observability, security, and privacy

### Log full execution traces

For every request, capture:

- **Prompt version and model version** — without these, results are not reproducible
- **Full trajectory** — every step, its inputs and outputs
- **Tool calls** — name, arguments, result, duration
- **Token counts** — input and output, per call
- **Cost** — per call and per request
- **Latency** — per step and end-to-end
- **Outcome** — success, failure, abandoned, escalated
- **Correlation ID** — tying it all together

This is the single highest-value investment in the system. It is what makes evaluation,
debugging, cost work, and incident response possible, and it is nearly impossible to
reconstruct after the fact.

### Mask PII before it reaches the model

Not after. Not in the logs afterward. Before the data leaves your boundary.

Identify what counts as PII in your domain, mask or tokenize it at the boundary, and keep
the mapping in your own systems. If the model needs to reference an entity, a token is
usually sufficient — the model rarely needs a real name to reason about an account.

Watch the indirect paths: stack traces, error messages, tool outputs, and retrieved
documents all carry PII more often than teams expect.

### Least privilege for every tool

Each tool gets exactly the access it needs. A tool that reads order status does not need
write access to the orders table. A tool that sends a notification does not need the
customer database.

Enforce this in the infrastructure — IAM, scoped credentials, network policy — not in the
prompt. The prompt is a hint; infrastructure is a control.

### The security properties worth naming

- **Model proposes, code decides.** Never let model output directly trigger an irreversible
  action
- **Validation is deterministic.** Ownership and permission checks in code, every time
- **Untrusted content cannot instruct.** Retrieved documents and user input are data
- **Tools are least-privilege.** Scoped credentials, not shared ones
- **Everything is logged.** Including denied and failed attempts

### Connect to the governance artifacts

This repository has the surrounding documentation these principles assume:

- [Security checklist](../security-checklist.md) · [Privacy checklist](../privacy-checklist.md) · [Governance checklist](../governance-checklist.md)
- [Model card template](../model-card-template.md) — document the models you route to
- [Datasheet template](../datasheet-template.md) — document the corpus you retrieve from
- [Incident runbook](../incident-runbook.md) — when it goes wrong

---

## The pre-production shortlist

If a system is about to serve real traffic, these are the ones that hurt most when missing:

- [ ] Every LLM and tool call has a timeout and a defined failure path
- [ ] Every loop is bounded — steps, wall-clock, tokens
- [ ] Execution state is persisted and workflows are resumable
- [ ] Full traces are logged with prompt and model versions
- [ ] Per-step cost and latency are visible
- [ ] Retrieval is evaluated separately from generation
- [ ] Untrusted content cannot reach an action without validation
- [ ] High-impact writes go through validation and human approval
- [ ] PII is masked before leaving your boundary
- [ ] Tools hold least-privilege credentials
- [ ] There is an eval set built from real traffic, and it runs on every change

Full version: [checklists/design-review.md](checklists/design-review.md).

---

## Related

- [ARCHITECTURE-PATTERNS.md](ARCHITECTURE-PATTERNS.md) · [BUILDING-BLOCKS.md](BUILDING-BLOCKS.md)
- [AGENT-SECURITY.md](../agentic-coding-playbook/AGENT-SECURITY.md) — prompt injection in depth
- [e2e-agent example](../../examples/e2e-agent/README.md) — includes SLA and governance docs
