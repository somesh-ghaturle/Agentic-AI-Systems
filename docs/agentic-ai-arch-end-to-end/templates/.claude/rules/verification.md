---
description: How to prove a change works before calling it done
globs: ["**/*"]
---

# Verification rules

## Definition of done

A task is done only when you have **run** the checks and **seen** them pass. Not when the
code looks right.

1. Relevant tests pass — paste the real output
2. Lint and format pass
3. Type check passes
4. The new behavior has a test that fails without your change

If you cannot run a check (no network, missing service, no credentials), say so explicitly
and name what is unverified. An honest gap is useful; a silent one is a bug in waiting.

## Evidence, not assertion

| Do not say | Say instead |
|---|---|
| "This should work." | "`pytest -q` → 47 passed, 0 failed." |
| "I fixed the bug." | "Added failing test `test_x`, confirmed red, applied fix, now green." |
| "Tests pass." | The actual command and its actual output. |
| "The UI looks right." | A screenshot, or the assertion that checks it. |

## Fix the root cause, never suppress the symptom

These are all forbidden as ways to make a check pass:

- Bare `except:` / `catch {}` that swallows the error
- Widening a type to `Any` / `any` / `object` to silence the checker
- `@skip`, `.skip`, `xfail`, or commenting out a failing test
- Loosening an assertion until it passes (`assertEqual` → `assertTrue`)
- Hardcoded values, stub data, or fallback dummies that fake a passing result
- `try/except: pass` around the actual failure
- Retry loops that hide a deterministic error

If the real fix is outside the current scope: **stop and report it.** Say what the root
cause is, what fixing it would touch, and let the human decide. Do not ship a green check
over a known-broken path.

## Write the failing test first

For any bug fix: reproduce it as a failing test *before* touching the implementation.
A fix without a red-then-green transition is unverified — you do not know whether it fixed
the bug or the bug was never what you thought.

## Layered checks

Run in this order, cheapest first, and stop at the first failure:

1. **Deterministic** — lint, types, unit tests, build. Fast and unambiguous.
2. **Integration** — real dependencies, slower, run before opening a PR.
3. **Judgment** — does this actually solve the reported problem? Does the diff contain
   anything unrelated to the task? This is the layer that catches passing-but-wrong.

Layer 3 is not optional just because layers 1 and 2 are green. Green tests on the wrong
solution is the most common way a change gets through and then gets reverted.
