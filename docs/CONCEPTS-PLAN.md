# Adding three concepts — harness, context, and graph engineering

A plan to cover three pieces of agentic-engineering vocabulary that this repository either
lacks or treats in passing, each with documentation, an honest sourcing entry, and a runnable
example.

Written 2026-08-14. Same conventions as [REPO-AUDIT.md](REPO-AUDIT.md) and
[HARDENING-PLAN.md](HARDENING-PLAN.md): work top to bottom, every task carries the command that
proves it worked, tick the boxes as you go.

## What is in scope, and what is deliberately not

Four terms were considered. One was dropped after reading what the repository already says.

**Loop engineering — excluded, already covered.** The concept is treated in four places:
[BUILDING-BLOCKS.md](agentic-system-architecture/BUILDING-BLOCKS.md) §4 sets pipeline against
autonomous loop and states the bounding rule;
[ARCHITECTURE-PATTERNS.md](agentic-system-architecture/ARCHITECTURE-PATTERNS.md) carries the
autonomous-loop pattern, the sentence "bounding an autonomous loop is not optional", and the
unbounded-loop antipattern; [PRODUCTION-PRINCIPLES.md](agentic-system-architecture/PRODUCTION-PRINCIPLES.md)
puts it in the pre-production checklist; and
[REFERENCES.md](agentic-system-architecture/REFERENCES.md) already sources it as established
practice. A fifth treatment under a new name would be duplication wearing a new label. The new
documents cross-link to it instead.

**Harness engineering — in scope, genuine gap.** Nothing in the architecture folder describes
the scaffolding around the model: what runs the agent, assembles its context, mediates its
tools, and decides when it is finished.

**Context engineering — in scope, near-total gap.** One passing mention in `REFERENCES.md` and
some adjacent vocabulary in the coding playbook's glossary. Nothing systematic, despite it being
the most firmly sourced term of the three.

**Graph engineering — in scope as a deepening, not a new document.** BUILDING-BLOCKS §4 already
has "What graph orchestration buys" and names LangGraph. That section gets extended rather than
replaced, because the concept is a way of building the orchestration layer that already exists
in the six blocks, not a seventh block.

## Sourcing

Every external reference below was fetched and read on 2026-08-14, not recalled. This matters
because `REFERENCES.md` separates claims by evidential weight, and a fabricated URL in a
document about provenance would be a particularly bad thing to ship.

| Concept | Source | Type |
| --- | --- | --- |
| Harness engineering | [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) | Primary — vendor engineering blog |
| Context engineering | [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) | Primary — vendor engineering blog |
| Graph orchestration | [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) | Primary — the implementation itself, MIT |

One correction this plan records against its own first draft: harness engineering was initially
assessed as informal vocabulary with no canonical source. That was wrong — the Anthropic post
above is a published treatment with named failure modes. The sourcing table reflects the
corrected assessment.

---

## Progress

| # | Task | Phase | Status |
|---|---|---|---|
| 1 | `HARNESS-ENGINEERING.md` | 1 | [x] |
| 2 | `examples/harness-agent/` — worked example with tests | 1 | [x] |
| 3 | Wire harness-agent into CI | 1 | [x] |
| 4 | `CONTEXT-ENGINEERING.md` | 2 | [x] |
| 5 | `examples/context-compaction/` — minimal reference | 2 | [x] |
| 6 | Deepen BUILDING-BLOCKS §4 on graph orchestration | 3 | [x] |
| 7 | `examples/graph-agent/` — minimal reference | 3 | [x] |
| 8 | Add all three to `REFERENCES.md` with honest labels | 4 | [x] |
| 9 | Update root README, architecture README, layout tree | 4 | [x] |

---

## Phase 1 — Harness engineering

### Task 1 — `docs/agentic-system-architecture/HARNESS-ENGINEERING.md`

A harness is what turns a model into an agent: the loop's runner, the context assembler, the
tool mediator, and the thing that decides the work is done. The document covers the four failure
modes the Anthropic post names — premature completion, over-ambition, incomplete testing, state
degradation — and the structural answers to each.

It must cross-link rather than restate: bounding belongs to §4 and the loop content, tool
contracts to §2, approval gates to §6.

### Task 2 — `examples/harness-agent/`

The worked example, at the [hermes-agent](../examples/hermes-agent/README.md) bar: package
layout, `architecture.md`, standard library only, and a test suite that gates merges.

**The design decision that makes this testable.** The example contains no model. A harness's
invariants are properties of the harness, not of the model it runs — so the "agent" here is a
stub that proposes actions from a script, and the tests assert the harness constrains it. That
is the same move `trace-eval` makes with its graders and `hermes-agent` makes with its router,
and it is what keeps the suite deterministic and runnable in CI without a key.

Each of the four named failure modes becomes an assertion:

| Failure mode | Harness invariant under test |
| --- | --- |
| Premature completion | `finish()` refuses while any feature is unverified |
| Over-ambition | A session accepts one feature; a second claim in the same session raises |
| Incomplete testing | A feature reaches `complete` only after its verifier returns pass |
| State degradation | The progress file is never left unparseable — writes are atomic |

**Verify:**

```bash
python3 -m unittest tests.test_harness_agent -v
python3 examples/harness-agent/agent.py          # the demo, end to end
```

### Task 3 — Wire it into CI

Add nothing to `example-deps.yml` — this example has no dependencies. It is picked up
automatically by `unittest discover -s tests` in the `examples` job of `checks.yml`, and by the
`compileall` step. Confirm rather than assume:

```bash
python3 -m unittest discover -s tests 2>&1 | tail -3
```

---

## Phase 2 — Context engineering

### Task 4 — `docs/agentic-system-architecture/CONTEXT-ENGINEERING.md`

Context rot and the n² attention argument for why more context is not free; the four strategies
the source names — compaction, structured note-taking, sub-agent architectures, just-in-time
retrieval; system-prompt altitude; and the tool-design overlap rule. Cross-links to §3 on memory
and state, and to `PRODUCTION-PRINCIPLES.md` on context and RAG design.

### Task 5 — `examples/context-compaction/`

Minimal reference tier: one script, one README. A message history that exceeds a token budget,
compacted by preserving decisions and open questions while dropping resolved detail — then a
before/after token count. Standard library, deterministic, no model.

---

## Phase 3 — Graph engineering

### Task 6 — Deepen BUILDING-BLOCKS §4

Extend "What graph orchestration buys" with what a graph actually gives you that a loop does
not: an explicit topology to inspect and test, resumable checkpoints at node boundaries,
first-class interrupts for approval gates, and per-node retry. Keep the existing pipeline-versus-
loop table; this is additive.

### Task 7 — `examples/graph-agent/`

Minimal reference using LangGraph, pinned. Unlike the other two examples in this plan it carries
a dependency, so it must be added to the `example-deps.yml` matrix with its entry module.

**Verify:**

```bash
python3 -m venv /tmp/graph-venv
/tmp/graph-venv/bin/pip install -r examples/graph-agent/requirements.txt
cd examples/graph-agent && /tmp/graph-venv/bin/python -c "import graph_agent"
```

---

## Phase 4 — Integration

### Task 8 — `REFERENCES.md`

Add the two Anthropic posts to "Primary documentation" and three rows to the concepts table.
Label honestly: the harness failure-mode taxonomy is primary-sourced; the claim that these
invariants are the *right* four to enforce is this repository's own framing.

### Task 9 — READMEs

The architecture README's document list, the root README's layout tree and examples section
(both new examples land in the minimal tier except harness-agent, which is a worked example),
and the example counts — currently "eight runnable examples" in three places.

---

## Definition of done

```bash
python3 -m compileall -q examples/
python3 -m unittest discover -s tests 2>&1 | tail -3
python3 .github/scripts/linkcheck.py .    # or the scratchpad copy until task 5 of HARDENING-PLAN lands
grep -c "runnable examples" README.md     # counts updated everywhere
```
