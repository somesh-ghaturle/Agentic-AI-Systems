# Roadmap

This roadmap is intentionally practical: it describes where the repository is today, what it is optimized to teach, and what the next milestones look like without promising production-grade deployment work that the examples do not contain.

## Current focus

The repository is centered on a small set of recurring ideas:

- A production agent must not reach a state-changing action without an explicit approval step tied to that action.
- Small examples are the primary teaching mechanism; they are easier to copy, reason about, and test than large demo apps.
- Infrastructure and policy examples should stay offline and deterministic where possible, especially in CI.
- Security hardening is approached as a design problem: guardrails, approval boundaries, traceability, and evals matter more than a large external dependency graph.

## Near-term milestones

### 1. Security and approval boundary examples

Keep expanding the examples that demonstrate the write boundary, prompt-injection resistance, and approval review flow.

Planned directions:
- More red-team and bypass-phrase variants across examples
- Clearer comparisons between naive models and guarded models
- More examples of trace review and approval evidence extraction

### 2. Governance and evidence quality

Continue tightening the quality bar for docs, security notes, and infrastructure assumptions.

Planned directions:
- Keep every example and security policy claim cross-linked to test coverage
- Improve the docs that explain how the repo draws the line between in-scope and out-of-scope issues
- Keep operational assumptions explicit when credentials and cloud access are intentionally absent from CI

### 3. Infrastructure clarity

The Terraform trees remain the deployment counterpart to the architecture examples. They should stay understandable, deterministic, and easy to compare across clouds.

Planned directions:
- Document the differences between the three cloud trees without overclaiming parity
- Keep policy-as-code and approval logic aligned with the repository's security model
- Show where the repo is intentionally not a full production cloud deployment guide

## Longer-term themes

### Architecture learning

The core teaching goal is to help readers build agentic systems that behave more like production software and less like chat wrappers.

Likely work:
- More explicit design patterns for tool contracts and memory boundaries
- Better examples of evaluation as a service and agent tracing
- More examples that make the approval boundary obvious in code and in event logs

### Adoption and reuse

The repo is designed to be copied into other projects. That means the most valuable future work is the work that makes it easier to adapt the patterns without losing the safety guarantees.

Likely work:
- clearer migration guidance for existing projects
- more structured example summaries and “what this teaches” notes
- better documentation for how to adopt only part of the architecture instead of the whole repo

## Status snapshot

The repository already includes:

- the core approval-boundary architecture examples
- the infrastructure trees for AWS, Azure, and GCP
- security and governance documents
- a CI posture built around offline validation and deterministic checks

The main remaining roadmap items are mostly documentation, governance, and community-facing improvements rather than large new architecture rewrites.

## Suggested next steps

1. Continue the queue of low-priority docs and community tasks in the enhancement plan.
2. Extend the example set only when it teaches a distinct security or architecture property.
3. Keep the examples small, standard-library-first, and test-backed so they remain easy to audit.
4. Prefer explicit approval traces and safety checks over hidden runtime assumptions.

This roadmap is designed to stay honest: it captures the trajectory of the repo without claiming that the examples are a fully managed production platform.
