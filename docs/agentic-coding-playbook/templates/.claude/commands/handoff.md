---
description: Dump session state to files so a fresh context can resume without relearning
---

# /handoff — save state before clearing context

Run this **before** clearing the context, before compaction, or at the end of a session.
The goal is that a fresh session with no memory of this conversation can pick up exactly
where this one stopped.

Update these files (create them if absent). Overwrite stale content — these are living
state, not append-only logs.

## `tasks.md`

```markdown
# Tasks

## Done
- [x] <what was completed, and how it was verified>

## In progress
- [ ] <what is half-done — name the exact file and function, and what state it is in>

## Blocked
- [ ] <what is blocked, on what, and who or what unblocks it>

## Next
- [ ] <the single next action a fresh session should take>
```

## `context.md`

```markdown
# Context

## Decisions made
- <decision> — because <reason>. Rejected <alternative> because <reason>.

## Constraints discovered
- <thing that turned out to be true and shaped the approach>

## Dead ends
- <approach that did not work, and why — so nobody retries it>

## Open questions
- <question, who can answer it, what we assumed in the meantime>
```

## `learnings.md` (append only)

Add anything the agent got wrong this session and the correction. Then say which of these
should be promoted into `CLAUDE.md` or a `.claude/rules/*.md` file — that promotion is the
step that stops the same mistake from recurring next week.

## Finally

Print a **three-line resume prompt** the user can paste into a fresh session:

```
Continue <project>. Read plan.md, tasks.md, and context.md first.
Next action: <the one specific next step>.
Watch out for: <the main gotcha discovered this session>.
```

Keep it tight. The value of the handoff is that the next session starts sharp instead of
re-deriving what this one already learned.
