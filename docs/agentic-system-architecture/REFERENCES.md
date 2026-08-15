# References and provenance

## A note on sourcing

This folder is a synthesis of established distributed-systems practice, published guidance
on LLM application design, and practitioner consensus. Those carry different evidential
weight, so they are separated below.

**Most of the load-bearing claims here are not novel.** Timeouts on external calls, bounded
retries, least-privilege credentials, and separating read from write paths are ordinary
engineering discipline that predates agents entirely. The agentic-specific content is
mostly about *where* to apply that discipline given a probabilistic component in the middle.

Where a claim is directional rather than measured, it is labeled below. Verify anything
before quoting it in a document that matters — particularly the storage and tooling
recommendations, which depend heavily on your actual scale and access patterns.

---

## Primary documentation

- **Model Context Protocol** — [modelcontextprotocol.io](https://modelcontextprotocol.io)
  The spec for exposing tools and data to agents.
- **Claude Docs** — [docs.claude.com](https://docs.claude.com)
  Tool use, structured outputs, prompt caching, model capabilities.
- **Anthropic Engineering blog** — [anthropic.com/engineering](https://www.anthropic.com/engineering)
  Agent design patterns, context engineering, evaluation.
- **Effective context engineering for AI agents** — [anthropic.com/engineering/effective-context-engineering-for-ai-agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
  Context rot, and the four long-horizon strategies. Primary source for [CONTEXT-ENGINEERING.md](CONTEXT-ENGINEERING.md).
- **Effective harnesses for long-running agents** — [anthropic.com/engineering/effective-harnesses-for-long-running-agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
  The four failure-mode names. Primary source for [HARNESS-ENGINEERING.md](HARNESS-ENGINEERING.md).
- **LangGraph** — [github.com/langchain-ai/langgraph](https://github.com/langchain-ai/langgraph)
  The reference implementation of graph orchestration. MIT.
- **OWASP Top 10 for LLM Applications** — [owasp.org/www-project-top-10-for-large-language-model-applications/](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
  Prompt injection is LLM01. Useful as a review structure.

---

## Concepts and where they come from

| Concept | Source type | Notes |
| --- | --- | --- |
| Single-agent before multi-agent | Practitioner consensus | Widely reported; the "decompose on evidence, not anticipation" framing is this document's own |
| Coordination overhead in multi-agent systems | Established distributed-systems practice | Predates agents — same reasoning as microservice decomposition |
| Model routing by step complexity | Practitioner consensus | Direction is well-supported; the specific tier table is illustrative, not measured |
| Structured outputs at every intermediate step | Primary docs + consensus | Tool-call and schema interfaces are documented capabilities |
| Read/write tool separation | Established security practice | Standard privilege separation applied to a new surface |
| "Model proposes, code decides" | This document's framing | The underlying control is ordinary authorization design |
| Execution / knowledge / archive state split | Practitioner consensus | Follows from access patterns; specific storage picks are illustrative |
| Pipeline over autonomous loop where sequence is known | Practitioner consensus | Strongly and consistently reported |
| Bounded loops (steps, time, tokens, no-progress) | Established practice | Ordinary runaway-process protection |
| The four harness failure modes | Primary docs | Named in the Anthropic harness post; the wording here follows it |
| "The agent is not a reliable narrator of its own progress" | This document's framing | The underlying point — self-reported completion is not evidence — is ordinary verification practice |
| Enforcing completion as a state transition | This repository's own | One implementation of the above, not the only one. See [harness-agent](../../examples/harness-agent/README.md) |
| No-progress bound as a distinct harness guard | This repository's own | Found by running [harness-agent](../../examples/harness-agent/README.md), not from a source. Bounding itself is established practice |
| Context rot and the n² attention argument | Primary docs | Stated in the Anthropic context post |
| Compaction, note-taking, sub-agents, just-in-time retrieval | Primary docs | The four strategies, named there |
| "Recency and relevance are different axes" | This document's framing | The consequence — truncation drops old decisions — is demonstrated in [context-compaction](../../examples/context-compaction/README.md) |
| What a graph buys over a loop | Practitioner consensus + primary | Durable interrupts and node-boundary resumption are documented LangGraph features; the four-row comparison is this document's own |
| Trace-level evaluation over final-output-only | Emerging practice | Direction well-supported; specific metrics vary by domain |
| LLM-as-a-judge validated against human labels | Emerging research + practice | Judge calibration is genuinely necessary and often skipped |
| Irrelevant context degrades reasoning | Emerging research | Direction supported; magnitude varies by model and task |
| Hybrid search and re-ranking improve retrieval | Established IR practice | Predates LLMs; well-measured in the IR literature |
| Prompt injection via retrieved documents | Established security research | OWASP LLM01; the RAG corpus as attack surface is well-documented |
| Full-trace logging as highest-value investment | Practitioner consensus | Strongly reported; also the most regretted omission |
| Prompt caching rewards stable-prefix ordering | Primary docs | Mechanism is documented; savings depend on your traffic shape |

---

## Storage and tooling mentions

Products named in [BUILDING-BLOCKS.md](BUILDING-BLOCKS.md) — Redis, DynamoDB, PostgreSQL,
MongoDB, Pinecone, pgvector, Weaviate, Elasticsearch, OpenSearch, S3, GCS — are
**illustrative of the category**, not recommendations. They are named because they are
commonly used for that access pattern, not because they were benchmarked for this document.

Orchestration options named — plain application code, state machines, LangGraph, temporal
workflow engines, LlamaIndex workflows — are likewise illustrative. The document's actual
position is that plain code is underrated for simple flows.

Pick based on what you already run, your scale, and your team's operational familiarity.

---

## Related frameworks

Relevant when this system needs to survive a governance review:

- **NIST AI Risk Management Framework** — [nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf)
- **EU AI Act** — [commission.europa.eu/publications/eu-artificial-intelligence-act_en](https://commission.europa.eu/publications/eu-artificial-intelligence-act_en)
- **Model Cards for Model Reporting** — [modelcards.withgoogle.com](https://modelcards.withgoogle.com/)
- **Hidden Technical Debt in Machine Learning Systems** — [papers.nips.cc/paper/5656-hidden-technical-debt-in-machine-learning-systems.pdf](https://papers.nips.cc/paper/5656-hidden-technical-debt-in-machine-learning-systems.pdf)
  Still the best account of why the model is the small part of the system.

---

## Related material in this repository

- [Agentic Coding Playbook](../agentic-coding-playbook/README.md) — using a coding agent well
- [AGENT-SECURITY.md](../agentic-coding-playbook/AGENT-SECURITY.md) — prompt injection in depth
- [Governance checklist](../governance-checklist.md) · [Security checklist](../security-checklist.md) · [Privacy checklist](../privacy-checklist.md)
- [Model card template](../model-card-template.md) · [Datasheet template](../datasheet-template.md)
- [Incident runbook](../incident-runbook.md)
- Runnable examples: [starter-agent](../../examples/starter-agent/README.md) · [rag-faiss](../../examples/rag-faiss/README.md) · [rag-langchain](../../examples/rag-langchain/README.md) · [ray-orchestrator](../../examples/ray-orchestrator/README.md) · [e2e-agent](../../examples/e2e-agent/README.md)

---

## Contributing

If a pattern here does not survive contact with your production system, or you have a
measured source for one of the directional claims above, open a PR. See
[CONTRIBUTING.md](../../CONTRIBUTING.md).
