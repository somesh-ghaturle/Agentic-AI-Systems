---
description: Investigate a task and write a reviewable plan to plan.md before any code is written
---

# /plan — plan first, execute second

Task: **$ARGUMENTS**

Do **not** write or edit any implementation code in this command. The only file you may
write is `plan.md`. The point is to make disagreement cheap — it costs minutes to fix a
wrong plan and hours to unwind a wrong implementation.

## Step 1 — Investigate before proposing

- Read the files this actually touches. Do not plan from filenames.
- Find the existing pattern for this kind of change in the codebase and follow it rather
  than inventing a new shape.
- Identify existing tests that cover this area, and where a new test belongs.
- Note anything already broken or surprising that affects the approach.

## Step 2 — Write `plan.md`

```markdown
# Plan: <task>

## Goal
One sentence. What is true after this is done that is not true now.

## Autonomy bucket
Green | Yellow | Red — and the one-line reason. See .claude/rules/autonomy.md

## Files to change
- `path/to/file.py` — what changes and why
- `tests/path/to/test_file.py` — what it will assert

## Approach
The steps, in order. Each one small enough to verify on its own.
1. ...
2. ...

## Acceptance criteria
How we will know it works. Concrete and runnable:
- [ ] `<test command>` passes
- [ ] New test `test_x` fails before the change, passes after
- [ ] <the specific observable behavior change>

## Out of scope
What this deliberately does not do. Prevents scope creep mid-implementation.

## Risks and unknowns
- What might be wrong about this plan
- What I could not determine from the code, and the assumption I am making instead
```

## Step 3 — Stop

Print the plan and **stop**. Do not begin implementing. Ask for review, and specifically
flag anything in "Risks and unknowns" that the human should decide before you start.
