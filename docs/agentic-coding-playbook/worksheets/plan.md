<!-- Copy to your repo root as plan.md. Written before code, read by a human, then executed. -->

# Plan: `<task name>`

**Status:** draft | approved | in progress | done
**Date:** `<YYYY-MM-DD>`

## Goal

One sentence. What is true after this is done that is not true now.

## Autonomy bucket

**Green | Yellow | Red** — because `<one line>`.
See your `.claude/rules/autonomy.md`.

## Context

What a fresh reader needs to understand the approach: why this is being done now, what
constrains it, what was already tried.

## Files to change

| File | Change | Why |
|---|---|---|
| `path/to/file.py` | `<what>` | `<why>` |
| `tests/path/test_file.py` | `<what it asserts>` | proves the change |

## Approach

Steps in order. Each one small enough to verify on its own before starting the next.

1. …
2. …
3. …

## Acceptance criteria

Concrete and runnable. Someone else should be able to check these without asking you.

- [ ] `<test command>` passes
- [ ] `test_<name>` fails before the change and passes after
- [ ] `<the specific observable behavior change>`
- [ ] Lint and type check clean

## Out of scope

What this deliberately does **not** do. This section is what stops scope creep at hour two.

- …

## Risks and unknowns

- **Risk:** `<what could go wrong>` → **Mitigation:** `<what we do about it>`
- **Unknown:** `<what I could not determine>` → **Assumption:** `<what I am assuming instead>`

## Rollback

How to undo this if it goes wrong in production. For Red-bucket work this is required, not
optional.
