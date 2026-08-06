# Agentic Coding Playbook

A drop-in kit for working with Claude (or any coding agent) as an **agent inside your
workflow** rather than a chatbot you consult.

The core shift is not prompt tricks. It is clear rules, small scopes, clean context,
verification commands, and review checkpoints. Those are what separate an impressive demo
from a practical system: tell the agent where to look, what not to touch, how to prove
success, and when to stop.

---

## What is in here

| Path | What it gives you |
|---|---|
| [PLAYBOOK.md](PLAYBOOK.md) | The eight habits, in the order you should build them |
| [TWO-WEEK-RAMP.md](TWO-WEEK-RAMP.md) | A concrete day-by-day adoption plan |
| [ANTIPATTERNS.md](ANTIPATTERNS.md) | Failure modes named so you catch them live |
| [ENTERPRISE-ADAPTATION.md](ENTERPRISE-ADAPTATION.md) | What changes in a governed environment (banks, health, gov) |
| [GLOSSARY.md](GLOSSARY.md) | Rules vs. commands vs. skills vs. subagents vs. MCP |
| [REFERENCES.md](REFERENCES.md) | Source material and further reading |
| [templates/](templates/) | Copy-paste starting files: `CLAUDE.md`, rules, commands, skills, agents |
| [checklists/](checklists/) | Task-start, pre-merge, and context-hygiene checks |
| [worksheets/](worksheets/) | `plan.md`, `context.md`, `tasks.md`, `learnings.md` scaffolds |

---

## Quick start (15 minutes)

```bash
# From the root of the repo you want to instrument:
PLAYBOOK=path/to/docs/agentic-ai-arch-end-to-end

cp $PLAYBOOK/templates/root/CLAUDE.md            ./CLAUDE.md
mkdir -p .claude/rules .claude/commands
cp $PLAYBOOK/templates/.claude/rules/*.md        .claude/rules/
cp $PLAYBOOK/templates/.claude/commands/*.md     .claude/commands/
cp $PLAYBOOK/worksheets/learnings.md             ./learnings.md
```

Then do the three things that make everything else work:

1. **Fill in the four commands** in `CLAUDE.md` — install, test, lint, build. If the agent
   cannot run your tests, it cannot verify its own work, and every habit below collapses
   back into "should work."
2. **Delete every line of `CLAUDE.md` you are not willing to enforce.** A short file that
   is all real rules beats a long file where the real rules are buried.
3. **Run one real task plan-first** — see [checklists/task-start.md](checklists/task-start.md).

---

## The one-paragraph version

Make an agentic surface (not a chat tab) your default. Give it thin, deliberate context.
Plan to a file before executing. Wire in a verification signal it can iterate against.
Choose autonomy per task instead of globally. Turn anything you have prompted twice into an
artifact. Keep sessions clean and single-purpose. And keep your own judgment in the loop,
because the bugs that survive are exactly the conceptual ones a human review catches and
the model does not.

---

## Reading order

New to this: [PLAYBOOK.md](PLAYBOOK.md) → [TWO-WEEK-RAMP.md](TWO-WEEK-RAMP.md) → copy the templates.

Already using agents daily and plateauing: skip to habit 6 in [PLAYBOOK.md](PLAYBOOK.md#6-anything-youve-prompted-twice-becomes-an-artifact),
then read [ANTIPATTERNS.md](ANTIPATTERNS.md). The plateau is almost always "never got past habit 1."

Rolling this out to a governed org: [ENTERPRISE-ADAPTATION.md](ENTERPRISE-ADAPTATION.md) first.
