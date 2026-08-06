# Design review

Run this twice: once on the design before building, and once on the implementation before
shipping. Most items are cheap to satisfy at design time and expensive to retrofit.

Items marked **⚠** are the ones that cause incidents when skipped.

---

## Architecture

- [ ] The single-agent vs. multi-agent choice is **written down with its reason**
- [ ] If multi-agent: there is evidence a single agent was insufficient, not just an
      expectation
- [ ] If multi-agent: every piece of shared state has exactly **one writer**
- [ ] The pattern is named — pipeline, router, orchestrator–worker, generator–critic, loop
- [ ] Deterministic pipeline is used wherever the sequence is known
- [ ] **⚠** Every autonomous loop is bounded: max steps, wall-clock timeout, token budget,
      no-progress detection

## Model layer

- [ ] Each step has a named model, chosen for a stated reason
- [ ] Cheap steps (classification, extraction, routing) are not on a frontier model by
      default
- [ ] **⚠** Every intermediate step returns a **structured contract**, not free text
- [ ] Schemas are versioned
- [ ] **⚠** Every model call has a defined fallback: retry, escalate, or fail cleanly
- [ ] Free-form text appears only in the final human-facing output

## Tool layer

- [ ] Every tool has name, description, input schema, output schema, timeout, permissions
- [ ] Tool descriptions are precise enough to drive correct selection
- [ ] **⚠** Read and write tools are **architecturally separated**
- [ ] **⚠** The model *proposes* writes; application code *decides*
- [ ] Every write is idempotent, with an idempotency key
- [ ] Tool results are bounded — no unbounded result sets into context
- [ ] Errors are structured and actionable, not stack traces
- [ ] Third-party tool servers have been vetted for what they access

## Memory and state

- [ ] Execution state, knowledge memory, and long-term archive are **separated**
- [ ] Storage choice matches access pattern for each
- [ ] **⚠** Execution state is persisted and serializable — workflows survive a restart
- [ ] State includes a correlation ID linking to traces
- [ ] Retrieval results are cacheable independently of the model layer
- [ ] **⚠** PII is masked before anything is written to the archive

## Orchestration

- [ ] The control flow is readable — someone new can trace a request through it
- [ ] Every step is resumable
- [ ] Every step is traceable under one correlation ID
- [ ] Failure paths are designed for each step, not discovered in production
- [ ] Framework choice is justified — plain code is a legitimate answer

## Evaluation

- [ ] **⚠** There is an eval set built from **real traffic**, not only synthetic cases
- [ ] Evaluation covers the trajectory, not just final output
- [ ] Intent, retrieval, tool selection, and argument formatting are each evaluated
- [ ] Deterministic checks are used wherever they apply, before any LLM judge
- [ ] Any LLM judge has been validated against human labels
- [ ] Test suites include edge cases, partial inputs, and **malicious inputs**
- [ ] Regression tests run on every prompt, model, or index change
- [ ] Cost and latency are tracked alongside quality

## Approval gates

- [ ] The list of gated actions is explicit and agreed
- [ ] **⚠** Ownership and permission validation happens in **code**, not the prompt
- [ ] Approval prompts show what, to whom, why, and the effect
- [ ] Gates are not so frequent that approval becomes reflexive
- [ ] Full approval records are logged: proposal, validation, approver, outcome

## Reliability

- [ ] **⚠** Every external call has a timeout
- [ ] Retries use backoff with jitter and a cap
- [ ] Schema validation on every model response, with a defined failure path
- [ ] Large prompts are decomposed into atomic steps
- [ ] Behavior on partial failure is defined — what state is left behind?

## Cost and latency

- [ ] Per-step cost and latency are measured and visible
- [ ] Token limits are enforced per step and per request
- [ ] Context does not grow unbounded across loop iterations
- [ ] Caching is in place for retrieval, policy lookups, and stable prompt prefixes
- [ ] User-facing output streams; intermediate reasoning does not
- [ ] There is a cost ceiling per request, and an alert before it

## Context and RAG

- [ ] Chunking respects semantic boundaries
- [ ] Metadata filtering happens **before** semantic search
- [ ] Hybrid search is used where exact terms matter (IDs, codes, names)
- [ ] Re-ranking is applied to final ordering
- [ ] **⚠** System instructions, user input, and retrieved content are **clearly separated**
- [ ] **⚠** Retrieved content can never directly trigger a write
- [ ] Retrieval is evaluated separately from generation
- [ ] Multi-tenant systems filter by tenant before search, not after

## Security and privacy

- [ ] **⚠** Tools hold least-privilege, scoped credentials — enforced in infrastructure
- [ ] PII is masked at the boundary, before the model sees it
- [ ] Indirect PII paths are considered: traces, errors, tool output, documents
- [ ] Untrusted content cannot instruct — injection mitigations are in place
- [ ] Denied and failed attempts are logged, not only successes
- [ ] Data retention and egress match your governance requirements

## Observability

- [ ] **⚠** Full execution traces are logged from day one
- [ ] Prompt version and model version are recorded on every request
- [ ] Token counts, cost, and latency are captured per call
- [ ] A single correlation ID ties a request end to end
- [ ] Traces are queryable — you can find "all requests where tool X failed"

## Governance

- [ ] A [model card](../../model-card-template.md) exists for the models in use
- [ ] A [datasheet](../../datasheet-template.md) exists for the retrieval corpus
- [ ] The [security](../../security-checklist.md) and [privacy](../../privacy-checklist.md)
      checklists have been run
- [ ] An [incident runbook](../../incident-runbook.md) covers this system
- [ ] Someone owns this system and is named

---

## The ten that matter most

If a review has time for only a subset:

1. Every autonomous loop is bounded
2. Every intermediate step returns a structured contract
3. Read and write tools are separated; the model proposes, code decides
4. Execution state is persisted and resumable
5. Every external call has a timeout and a defined failure path
6. Full traces are logged with prompt and model versions
7. There is an eval set from real traffic that runs on every change
8. Retrieved and user content cannot instruct or trigger writes
9. PII is masked before leaving your boundary
10. Tools hold least-privilege credentials enforced in infrastructure

---

## Related

- [ARCHITECTURE-PATTERNS.md](../ARCHITECTURE-PATTERNS.md) · [BUILDING-BLOCKS.md](../BUILDING-BLOCKS.md) · [PRODUCTION-PRINCIPLES.md](../PRODUCTION-PRINCIPLES.md)
