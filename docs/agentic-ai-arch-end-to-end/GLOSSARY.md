# Glossary

The five extension mechanisms get confused constantly. The distinction that matters is
**what each one is made of** and **when it costs you context**.

## The decision table

| You have | Use a | Because it is | Costs context |
|---|---|---|---|
| A fact about the project | **Context file** (`CLAUDE.md`) | Always-on instruction | Every turn — keep it thin |
| A rule for one subtree | **Rule** (`.claude/rules/*.md`) | Instruction scoped by path glob | Only in that subtree |
| A prompt you have typed twice | **Command** (`.claude/commands/*.md`) | A reusable prompt you invoke | Only when invoked |
| Knowledge it keeps needing | **Skill** (`.claude/skills/*/SKILL.md`) | Reference material, loaded on demand | Description only, until it fires |
| Work that generates noise | **Subagent** (`.claude/agents/*.md`) | A separate context reporting a result | Only the final report |
| A connection to another system | **MCP server** | A tool integration | Tool definitions |

---

## Context file — `CLAUDE.md`

What the agent cannot infer: stack, commands, conventions, boundaries. Read from org
settings, your home directory, the project root, and subdirectories, composing together.

**Loaded every turn.** That is why the ~200-line cap matters — it is a permanent tax on
every request in the project.

## Rule — `.claude/rules/*.md`

A context file scoped by path. The `globs:` line in the frontmatter decides when it loads.

This is the pressure valve for `CLAUDE.md`: deep, specific rules for the payments module
that never load while you are editing docs.

## Command — `.claude/commands/*.md`

A saved prompt, invoked by name (`/plan`, `/verify`). Contains **instructions**, not
knowledge — the steps to take, in order.

The trigger to write one is mechanical: **you typed it twice.**

## Skill — `.claude/skills/*/SKILL.md`

Domain **knowledge**, loaded on demand. Only the `description` stays resident; the body
loads when the description matches what is happening.

That asymmetry is the whole design: descriptions must be precise, bodies can be generous.
Skills can carry supporting files that load only when reached.

**Command vs. skill:** a command is a verb (do this sequence), a skill is a noun (know this
thing). "Prepare a release" is a command. "How our pricing rules actually work" is a skill.

## Subagent — `.claude/agents/*.md`

A separate context that does work and reports back a result. Your main context sees only the
final message, not the intermediate exploration.

Use for anything noisy: broad searches, research, large refactors across many files.

**Make them feature-specific.** "Checkout flow agent" with your real paths beats "backend
engineer" every time — vague descriptions produce poor tool selection and loose context.

## MCP server

Model Context Protocol — a standard way to expose external tools and data (a ticket
tracker, a database, an internal service) to the agent.

**Skill vs. MCP:** a skill tells the agent *how to think* about something. An MCP server
gives it *something to call*. Knowledge versus capability.

---

## Other terms

**Agentic surface** — an environment where the model has your filesystem, your shell, and a
loop, as opposed to a chat window where it has only text you paste.

**Context hygiene** — keeping a session to one task, clearing between tasks, and dumping
state to files before clearing.

**Compaction** — automatic summarization when a conversation grows too long. Detail is lost.
Run a handoff *before* it happens so the state lives in files instead.

**Evidence-based completion** — a task is done when checks have been run and shown passing,
not when the code looks right. "Should work" is not a result.

**Deterministic verifier** — a check with an unambiguous pass/fail: tests, lint, types,
build. Cheap, run first.

**LLM judge** — a model evaluating work against criteria a deterministic check cannot
express ("does this actually solve the reported problem?"). Runs after the cheap checks and
catches passing-but-wrong.

**Autonomy bucket** — Green / Yellow / Red. How much supervision a task gets, decided
before it starts. See [autonomy.md](templates/.claude/rules/autonomy.md).

**Root-cause fix vs. symptom suppression** — the difference between fixing the bug and
making the check stop reporting it. Bare excepts, widened types, skipped tests, and
hardcoded fallbacks are all suppression.

**Conceptual bug** — a defect in the logic rather than the syntax: inverted condition, wrong
boundary, right-for-the-happy-path. Type-checks cleanly, survives tests that encode the same
misunderstanding, and is the dominant remaining bug class in generated code.
