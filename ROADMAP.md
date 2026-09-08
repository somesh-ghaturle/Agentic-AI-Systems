# Roadmap

Where the repository is, what it is optimised to teach, and what is worth doing next. It
deliberately does not promise production deployment work the examples do not contain.

## What this repository is for

One property organises everything here: **a state-changing action cannot reach production
without a human approving that specific action.** The examples, the Terraform trees, the
threat model, and the CI checks are all arguments for that property or tests of it.

Two supporting commitments follow from it:

- **Small examples over demo applications.** Something you can read in one sitting, run with
  no key, and copy into your own tree teaches more than a large app that only runs on a
  machine configured like the author's.
- **Offline and deterministic in CI.** No cloud credentials, no model calls, no network in the
  default jobs. This constrains what CI can prove, and the gaps are named rather than papered
  over — see [`ENVIRONMENT-ENGINEERING.md`](docs/agentic-system-architecture/ENVIRONMENT-ENGINEERING.md) §4.

## Status snapshot

| Area | Where it stands |
| --- | --- |
| Examples | 23, stdlib-first, each with tests in `tests/` |
| Tests | 367, running on both the 3.9 floor and current Python |
| Architecture chapters | 4 disciplines — context, harness, evaluation, environment — plus patterns, building blocks, production principles |
| Diagrams | 47 interactive HTML viewers, each embedded in its document as a GIF |
| Terraform trees | 5 — AWS, Azure, GCP, Snowflake, and an opt-in cross-cloud hybrid POC |
| CI | 14 jobs; CodeQL over Python and workflows on a schedule |
| Decision logs | 5 ADRs |
| Enhancement plan | 67 tasks, all `Done` |

The enhancement plan is the detailed record; this file is the direction.

## Where the work actually is now

The four architecture chapters are the spine, and each one has runnable code behind it. That
pairing is the thing to protect: a chapter with no example drifts into assertion, and an
example with no chapter is a trick nobody can generalise from.

| Chapter | Runnable counterpart |
|---|---|
| [Context](docs/agentic-system-architecture/CONTEXT-ENGINEERING.md) | `context-compaction`, `context-overflow` |
| [Harness](docs/agentic-system-architecture/HARNESS-ENGINEERING.md) | `harness-agent` |
| [Evaluation](docs/agentic-system-architecture/EVALUATION-ENGINEERING.md) | `trace-eval`, `eval-red-teaming` |
| [Environment](docs/agentic-system-architecture/ENVIRONMENT-ENGINEERING.md) | `second-path`, `budget-guard`, `checkpoint-agent` |

## Near-term

### 1. Keep the chapters and the code in step

The highest-value maintenance in this repository is not new material. It is noticing when a
chapter and its example stop agreeing, or when a checklist stops covering a chapter — which
already happened once: the design review ran for two chapters without covering either, while
both were documented at length.

- Every new claim in a chapter should be traceable to a test, or marked as directional
- Every example should name the chapter it belongs to, and vice versa
- `REFERENCES.md` should keep separating measured from directional, including for claims that
  are this repository's own

### 2. Security and approval boundary examples

The area with the most room left, and the one most on-theme.

- More red-team and bypass-phrase variants, and more comparisons between naive and guarded
  paths that are honest about the naive one being reasonable-looking
- More ways the boundary is lost that are *not* the gate being wrong — `second-path` covers a
  second route to the effect, and `tool-discovery` covers a filter instead of a structure;
  there are others
- More trace review and approval-evidence extraction

### 3. Infrastructure honesty

The Terraform trees are the deployment counterpart to the architecture. They should stay
comparable across clouds without overclaiming parity.

- Document where the trees genuinely differ rather than smoothing it over
- Keep policy-as-code aligned with the security model
- Close the diagram gap: the hybrid tree is the only architecture document without one
- Keep saying plainly where this stops being a production deployment guide

## Longer-term

### Adoption without losing the guarantees

The repository is designed to be copied. The most valuable future work makes it easier to
adopt *part* of it without silently dropping the property that makes it worth adopting.

- Clearer guidance for taking one boundary into an existing codebase
- Per-example "what this teaches, and what it does not" notes, which several examples have and
  the rest should
- Migration guidance that survives someone skipping a step

### What is deliberately not here

Recorded so the absence reads as a decision rather than an oversight:

- **No IaC security scanner.** CodeQL has no Terraform analyser, and roughly half this
  repository is `infra/`. Closing that needs Checkov, tfsec, or trivy, and is its own decision.
- **No `terraform plan` in CI.** It needs cloud credentials, and the no-secrets constraint is
  worth more than the extra coverage. The write-boundary suites read source instead.
- **No benchmark numbers.** `trace-eval` shows a method over seven hand-written cases. It is
  not a score worth quoting, and saying so is part of the point.

## How to pick the next thing

1. Prefer closing a gap between what a document claims and what the tree does over adding new
   material. Those gaps are the failure this repository keeps naming.
2. Extend the example set only when it teaches a distinct security or architecture property.
3. Keep examples small, standard-library-first, and test-backed, so they stay auditable.
4. Prefer explicit approval traces and boundary tests over runtime assumptions.
