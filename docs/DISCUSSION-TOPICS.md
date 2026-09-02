# Discussion Topics

This repository is most useful when people discuss the trade-offs behind the examples, not just copy the code. The topics below are intended as ready-to-use GitHub Discussion prompts for architecture, safety, governance, and adoption conversations.

## Starter discussion prompts

### 1. Approval gates are a product decision, not a prompt trick
- What kinds of approval flows are appropriate for different classes of actions?
- Should the same approval policy apply to read/write tools, model-bound actions, and infrastructure changes?
- Where do you draw the line between a human approval and a policy-enforced guardrail?

### 2. Making the write boundary easy to reason about
- How do you make a write boundary obvious in a real application instead of hidden inside a tool call?
- What metadata should every write action carry before it reaches production?
- What signal is most useful in a trace: the final answer, the tool payload, or the approval record?

### 3. Examples that must stay small and explicit
- What makes an example portable enough to copy into another repo without hiding important assumptions?
- How much operational context should a minimal example include before it stops being minimal?
- When should an example include a disclaimer instead of an actual production claim?

### 4. Evaluation and red-teaming
- Which evaluation failures are most likely to fool a model into appearing compliant while still doing the wrong thing?
- How should prompt-injection drills be used in a CI workflow without turning them into a brittle snapshot test?
- What evidence is needed to trust a guard that blocks a bypass attempt?

### 5. Deployment and operational constraints
- How do you keep infrastructure checks offline and deterministic when the real cloud can drift at runtime?
- When should a repo depend on cloud credentials in CI, and when is the better answer to keep the job local-only?
- Which checks belong in pre-merge validation versus live production monitoring?

## Suggested discussion categories

Use GitHub Discussions to group conversation by actual decision area rather than by implementation detail:

- Architecture: patterns, trade-offs, and deployment choices
- Safety and governance: approval flows, policy boundaries, and incident review
- Examples and adoption: how to copy or adapt the patterns into another project
- Evaluation: testing models, tracing actions, and red-teaming prompts
- Operations: runbooks, recovery steps, and environment hygiene

## Discussion template

Copy this into a new discussion when you want to start a thread around a design decision:

```md
### Context
What problem are we trying to solve, and what are the constraints?

### Current approach
What is the repository doing today, and what trade-offs are intentionally accepted?

### Decision to explore
What decision needs feedback from the broader community?

### Options
1. Option A: ...
2. Option B: ...
3. Option C: ...

### Risks
What would make this choice unsafe or hard to maintain?

### Evidence
What examples, tests, or runbooks already point in one direction?
```

## Good discussion examples for this repository

- Architecture review: "Should every write action carry an explicit approval record?"
- Safety review: "How should this repo classify prompt-injection examples in security policy?"
- Example design: "What should a minimal example include when it is meant to teach a pattern rather than demonstrate a production service?"
- Adoption feedback: "Which parts of the repo are easiest to reuse in a regulated enterprise environment?"

## Keep it useful

The goal is not to convert every issue into a long design discussion. Use GitHub Discussions for trade-offs, lived experience, and examples that benefit from community feedback; use GitHub issues for concrete defects and repo-specific fixes.
