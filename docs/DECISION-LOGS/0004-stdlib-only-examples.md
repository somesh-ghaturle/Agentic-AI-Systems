# ADR 0004 — An example gets a dependency only when the dependency is the subject

**Status: Accepted** · Decided 2026-08-02 · Scope: `examples/`, `.github/workflows/`

> **Correction to the plan text.** The task that produced this record described the rule as
> "most examples use only the Python standard library", with LangChain and Ray as the
> exceptions. Counted on 2026-08-23 that is not the split: it is **six of twelve**, and the
> exceptions run wider than two frameworks.

## Context

Twelve examples, as of 2026-08-23:

| Stdlib only | Carries pins | Why the pin |
|---|---|---|
| `checkpoint-agent` | `e2e-agent` | `fastapi`, `uvicorn`, `pydantic`, `opentelemetry-{api,sdk}` |
| `context-compaction` | `graph-agent` | `langgraph` |
| `harness-agent` | `langchain-agent` | `langchain-core`, `langchain-openai` |
| `hermes-agent` | `rag-faiss` | `sentence-transformers`, `faiss-cpu`, `numpy` |
| `starter-agent` | `rag-langchain` | the `rag-faiss` set plus LangChain |
| `trace-eval` | `ray-orchestrator` | `ray[default]` |

Half of them are the load-bearing half. `starter-agent`, `harness-agent`,
`context-compaction`, `hermes-agent`, `trace-eval`, and `checkpoint-agent` teach orchestration,
context engineering, harness design, trace evaluation, and checkpointing — none of which is a
claim about a library. The other six exist to show a specific framework doing a specific thing,
and there is no way to show that without installing it.

## Decision

From [`CONTRIBUTING.md`](../../CONTRIBUTING.md):

> **Standard library only**, unless the dependency *is* the subject of the example.

With three rules that follow from it:

1. **Every example carries a `requirements.txt`**, empty ones included, holding a comment that
   says why it is empty. An absent file is indistinguishable from an unfinished one.
2. **Pins are exact, direct-only, dated**, with a sentence on why the dependency is there.
   Floors are not used — a floor makes CI's answer depend on the day it ran.
3. **Tests are stdlib `unittest`.** Not pytest: it is in no requirements file here, and a suite
   written against it would not run. A suite for an example with dependencies must **skip**
   without them rather than fail.

## Consequences

- A stdlib-only example runs on a clean Python 3.12 with no install step. That property is what
  is being bought, and it is what makes the majority of this repository readable as a
  demonstration rather than a project to set up.
- **CI splits along exactly this line, and has to.**
  [`checks.yml`](../../.github/workflows/checks.yml) installs nothing, runs the stdlib suites,
  and `compileall`-parses all of `examples/` in about a second — affordable on the unfiltered
  trigger. [`example-deps.yml`](../../.github/workflows/example-deps.yml) installs the pins and
  imports the entry modules for the six that have them; it pulls Torch, Ray and FAISS, so it
  gets its own trigger. `on.paths` is per-workflow, not per-job, which is why that is a separate
  file rather than a separate job.
- **Parsing is not importing**, and the gap between them is a failure this repository actually
  had: `rag-langchain` and `langchain-agent` imported `langchain.chains.LLMChain`, the pinned
  `langchain-core` had already deleted it, and CI was green throughout. A stale pin is invisible
  to every check that does not install the pin.
- The cost is that the six framework examples are the ones that rot, and they rot silently
  between Dependabot runs. That is the accepted price of showing the frameworks at all.

## Alternatives considered

1. **One shared `requirements.txt` at the repository root.** Rejected: it makes every example
   carry every other example's dependencies, and the stdlib-only property — the reason most of
   these run anywhere — disappears the moment one example needs Torch.
2. **Floor constraints (`>=`) instead of exact pins.** Rejected. A floored example passes CI on
   Monday and fails on Tuesday for a reason no commit in this repository caused, and the
   resolution date recorded next to the pin is what makes a break attributable.
3. **No framework examples at all.** Rejected — `langgraph`, LangChain, and Ray are what a
   reader is actually choosing between, and refusing to show them makes the repository purer
   and less useful.

## What would reopen this

An example whose subject genuinely requires a framework gets one, with a pin and a sentence.
That is the rule working, not an exception to it. What would *change* the rule is the
stdlib-only half falling below a handful of examples, at which point the split is no longer
worth the two-workflow arrangement that supports it.

## Fixed while writing this

`checkpoint-agent` (added under enhancement task 8) had no `requirements.txt` at all, which rule
1 above forbids. It now carries a comment-only one. The stale counts in `CONTRIBUTING.md`
("seven of eleven") and in `example-deps.yml`'s comments ("all eight") were corrected to match
the twelve examples that exist.
