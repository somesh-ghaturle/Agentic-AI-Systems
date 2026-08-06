# References and provenance

## A note on sourcing

This playbook was assembled from a mix of primary documentation, practitioner writing, and
reported experience. Those have different evidential weight, so they are separated below.

Several specific figures in circulation — an LLM-judge veto rate of roughly a quarter of
sessions at Spotify, benchmark scores in the low-to-mid 80s on realistic engineering tasks,
the "eighty-percent solution" auto-accept practice on the Claude Code team, and the
subagent guidance attributed to Boris Cherny — reached this document through secondary
write-ups rather than verified primary sources. **Treat them as illustrative rather than
citable.** They are directionally useful and the habits do not depend on the exact numbers:
"an LLM judge catches a meaningful share of work that passed deterministic checks" is the
load-bearing claim, not the specific percentage.

Verify anything before quoting it in a document that matters.

---

## Primary documentation

Start here. This is the material that is authoritative and stays current.

- **Claude Code documentation** — [code.claude.com/docs](https://code.claude.com/docs)
  Context files, rules, commands, skills, subagents, hooks, permissions, MCP, settings.
- **Claude Docs** — [docs.claude.com](https://docs.claude.com)
  Model capabilities, tool use, prompt caching, the API surface.
- **Model Context Protocol** — [modelcontextprotocol.io](https://modelcontextprotocol.io)
  The spec for exposing external tools and data to agents.
- **Anthropic Engineering blog** — [anthropic.com/engineering](https://www.anthropic.com/engineering)
  Agent design patterns, context engineering, evaluation.

---

## Concepts and where they come from

| Concept | Source type | Notes |
| --- | --- | --- |
| Context file layering (org → user → project → subdirectory) | Primary docs | Verifiable in the docs |
| Commands, skills, subagents, MCP | Primary docs | Verifiable in the docs |
| Keep context thin; short beats long | Practitioner consensus | Widely reported; the ~200-line cap is a heuristic, not an official limit |
| Plan-first, persist state to files | Practitioner writing | Well-established pattern, independently arrived at by many teams |
| Verification in the loop / evidence-based completion | Practitioner consensus + primary guidance | The most consistently reported high-leverage habit |
| Deterministic verifiers + LLM judge | Reported industry practice | Pattern is solid; specific veto rates unverified |
| Per-task autonomy calibration | Reported practice | The Green/Yellow/Red framing is this document's own |
| "Prompted twice → artifact" | Practitioner heuristic | A rule of thumb, and a good one |
| Feature-specific over role-generic subagents | Attributed practitioner guidance | Attribution unverified; the underlying reasoning is sound and independently testable |
| Non-engineering uses (legal, marketing, data science) | Reported internal Anthropic experience | Directionally reported in Anthropic material |
| Shift in bug taxonomy toward conceptual errors | Emerging research + practitioner reports | Direction is well-supported; magnitudes vary by study |
| Prompt injection as the dominant agent risk | Established security research | OWASP LLM01; the "instructions and data share a channel" framing is well-established |
| Capability limits over content filtering | Security consensus | Standard defense-in-depth reasoning, not specific to any vendor |
| Shared vs. personal config split | This document's own | Derived from ordinary git practice; no external source claimed |
| Cost driven by session shape, not headcount | Mechanical | Follows from how context is re-sent per turn; verify against your own billing |
| Characterization tests for legacy code | Established practice | Predates agents entirely — see Feathers, *Working Effectively with Legacy Code* |

---

## Governance and risk

Relevant when adapting this for a regulated environment — see
[ENTERPRISE-ADAPTATION.md](ENTERPRISE-ADAPTATION.md).

- **NIST AI Risk Management Framework** — [nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf)
- **EU AI Act** — [commission.europa.eu/publications/eu-artificial-intelligence-act_en](https://commission.europa.eu/publications/eu-artificial-intelligence-act_en)
- **OWASP Top 10 for LLM Applications** — [owasp.org/www-project-top-10-for-large-language-model-applications/](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- **Model Cards for Model Reporting** — [modelcards.withgoogle.com](https://modelcards.withgoogle.com/)
- **Hidden Technical Debt in Machine Learning Systems** — [papers.nips.cc/paper/5656-hidden-technical-debt-in-machine-learning-systems.pdf](https://papers.nips.cc/paper/5656-hidden-technical-debt-in-machine-learning-systems.pdf)
  Predates the agent era and remains the best account of why the code is the easy part.

---

## Related material in this repository

- [Governance checklist](../governance-checklist.md)
- [Security checklist](../security-checklist.md)
- [Privacy checklist](../privacy-checklist.md)
- [Model card template](../model-card-template.md)
- [Datasheet template](../datasheet-template.md)
- [Incident runbook](../incident-runbook.md)
- [End-to-end agent example](../../examples/e2e-agent/README.md)

---

## Contributing

This playbook improves the same way the practice does — by folding real experience back in.
If you find that a habit does not survive contact with your codebase, or you have a primary
source for one of the unverified claims above, open a PR. See
[CONTRIBUTING.md](../../CONTRIBUTING.md).
