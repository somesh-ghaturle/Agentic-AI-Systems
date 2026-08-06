# Task-start checklist

Thirty seconds before you type the prompt. Most bad agent sessions are decided here, not
in the middle.

## Scope

- [ ] I can state the goal in **one sentence** — what is true after that is not true now
- [ ] I know which **files** this touches (roughly), and I said so in the prompt
- [ ] I know what is **out of scope** and said that too
- [ ] The task is **one task** — if it is three, it is three sessions

## Context

- [ ] This session is **empty or on-topic** — not carrying an unrelated earlier task
- [ ] `CLAUDE.md` exists and its commands actually run
- [ ] Any scoped rules for this area are in `.claude/rules/` and current
- [ ] I pointed at the specific files rather than making it search the whole tree

## Verification — the one that matters

- [ ] There is an **objective signal**: test, lint, build, script, or screenshot
- [ ] I said in the prompt **how success will be proven**, not just what to build
- [ ] For a bug: a **failing test comes first**, before any fix
- [ ] If no signal exists, creating one **is** the first task

> If you skip only one line on this checklist, do not let it be this section. Without a
> verification signal you are trading real review time for the phrase "should work."

## Autonomy

- [ ] I picked a bucket: **Green / Yellow / Red** (see [autonomy.md](../templates/.claude/rules/autonomy.md))
- [ ] Auto-accept is **off** if this is Yellow or Red
- [ ] If Red, I have budgeted time to read every line

## Plan

- [ ] For anything non-trivial: **plan to a file first**, read it, correct it, then run
- [ ] The plan has acceptance criteria I could hand to someone else
- [ ] I actually read the plan rather than skimming and approving it

## The prompt itself

A good prompt names four things:

1. **Where to look** — the files or directories
2. **What to do** — the goal, in one sentence
3. **How to prove it** — the command or observable outcome
4. **What not to touch** — boundaries and out-of-scope

Example:

> In `src/checkout/promos.py`, fix stacking so percentage codes apply before fixed-amount
> codes. Write a failing test in `tests/checkout/test_promos.py` first, then fix.
> Verify with `pytest tests/checkout -q`. Do not touch `src/payments/` or the state machine.
