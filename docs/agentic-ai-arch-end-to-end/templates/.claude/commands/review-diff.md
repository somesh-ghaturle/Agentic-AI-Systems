---
description: Review the working diff for conceptual bugs — the class automated checks miss
---

# /review-diff — hunt the bugs the tests do not catch

Review the current diff (`git diff` plus staged and untracked files). Assume lint, types,
and tests are already green — this review is for the class of defect that passes all three.

## Why this exists

The bug taxonomy for generated code has shifted away from syntax errors toward subtle
conceptual errors that type-check cleanly. Passing tests often encode the same
misunderstanding as the code, so green is weak evidence in an area with real logic. This
pass targets exactly that gap.

## Look for, in priority order

**1. Conceptual errors**
- Off-by-one, inverted conditions, wrong boundary (`<` vs `<=`)
- Wrong variable used where a similarly named one was meant
- Logic that is right for the happy path and wrong for empty / single / duplicate input
- Misread of what the surrounding code actually guarantees

**2. Suppressed symptoms**
- Bare `except` / `catch {}`, `try: … pass`
- Types widened to `Any` to silence the checker
- Skipped, deleted, or loosened tests
- Hardcoded values or fallback stub data standing in for real behavior

**3. Correctness at the edges**
- Empty collection, null, zero, negative, very large
- Duplicate or out-of-order input
- Concurrent access to shared state
- Partial failure — what is left behind if this errors halfway?

**4. Dirty code**
- Loops or branches that cannot be reached, or that do nothing
- Redundant recomputation inside a loop
- Abstraction invented for a single caller
- Code that does not match the style of the file it lives in

**5. Scope**
- Anything in the diff unrelated to the stated task
- New dependencies
- Changes to files listed under Boundaries in `CLAUDE.md`

## Output

For each finding:

```
file.py:42 — <one-line claim>
  Failure: <concrete input or state → wrong output or crash>
  Fix: <the specific change>
```

Rank by severity. Then state plainly whether you would merge this. If the diff is clean,
say so in one line — do not manufacture findings to look thorough.
