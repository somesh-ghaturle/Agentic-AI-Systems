---
description: Run every project check and report the real output — no "should work"
---

# /verify — prove it works

Run the full verification stack for this project and report actual results.

## Run these, in order, stopping at the first failure

Use the commands from `CLAUDE.md`. If a command is missing there, say so — a project
without a runnable test command cannot be verified, and that is the finding.

1. **Lint / format**
2. **Type check**
3. **Unit tests**
4. **Build**
5. **Integration tests** (if the required services are available)

## Report format

```
| Check      | Command                | Result                    |
|------------|------------------------|---------------------------|
| Lint       | `ruff check .`         | ✅ clean                  |
| Types      | `mypy src`             | ✅ 0 errors               |
| Tests      | `pytest -q`            | ❌ 2 failed, 45 passed    |
| Build      | `uv build`             | ⏭️ skipped — tests failed |
```

Then, for each failure: the actual error output, the file and line, and your read on the
root cause.

## Rules

- **Paste real output.** Never summarize a result you did not observe.
- **Do not fix anything in this command** unless asked. Report first — a fix bundled with
  a diagnosis hides which one you were confident about.
- If a check cannot run (missing service, no credentials, no network), mark it
  **unverified** and say why. Do not mark it passed, and do not quietly skip it.
- If everything passes, say so plainly with the numbers. No hedging.

## Then answer the judgment question

Deterministic checks being green is necessary, not sufficient. Also assess:

- Does the change actually solve the problem that was reported?
- Does the diff contain anything unrelated to the task?
- Are there untested paths in what changed — empty input, duplicates, concurrent access,
  hostile input?
- Was any check made to pass by suppressing a symptom rather than fixing a cause?
