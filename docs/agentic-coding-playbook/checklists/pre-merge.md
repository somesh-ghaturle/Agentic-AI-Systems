# Pre-merge checklist

Before agent-assisted work becomes someone else's problem.

## Evidence, not assertion

- [ ] Tests **run** and pass — I saw the output, I did not read a claim about it
- [ ] Lint and type check pass
- [ ] Build succeeds
- [ ] The new behavior has a test that **fails without the change** (verified red → green)
- [ ] Anything unverifiable is named explicitly as unverified

## No suppressed symptoms

Scan the diff specifically for these. They are how a broken change turns green:

- [ ] No bare `except:` / `catch {}` / `try: … pass`
- [ ] No types widened to `Any` / `any` to silence a checker
- [ ] No skipped, deleted, or loosened tests
- [ ] No hardcoded values or stub data faking a real result
- [ ] No retry loop hiding a deterministic failure
- [ ] Every fix addresses a **cause**, not a symptom

## Conceptual review — read the diff, not the summary

The summary was written by the same process that wrote the code. It describes intent; the
diff is what ships.

- [ ] I read **every changed line**, not a summary of them
- [ ] Boundaries: empty, null, zero, negative, duplicate, very large
- [ ] Conditions and comparisons are right (`<` vs `<=`, inverted logic)
- [ ] Partial failure leaves a sane state
- [ ] Concurrency and shared state considered where relevant
- [ ] **Extra suspicion on anything that worked on the first try in a Red area**

## Cleanliness

- [ ] No unreachable branches, no loops that do nothing
- [ ] No abstraction invented for a single caller
- [ ] Code matches the style of the file around it
- [ ] Debug output, commented-out code, and TODOs removed or justified

## Scope

- [ ] Diff contains **only** what the task called for
- [ ] No unrequested new dependencies
- [ ] No changes to Boundaries paths without explicit sign-off
- [ ] No secrets, keys, tokens, or real customer data anywhere in the diff

## Fold the loop back

- [ ] Anything the agent got wrong is written into `learnings.md`
- [ ] Anything recurring is promoted into `CLAUDE.md` or a `.claude/rules/*.md`

That last pair is what makes next week cheaper than this week. Skipping it is why some
teams run agents for six months and are no faster than on day one.

## If someone else will review this

- [ ] The PR states the **autonomy bucket** — it tells the reviewer how hard to look
- [ ] The **verification output is pasted in**, not summarized. `/verify` produces a table
      built for this
- [ ] Nothing personal or machine-specific leaked into committed config (local paths,
      credentials, your own scratch notes)
- [ ] Session state files (`plan.md`, `tasks.md`, `context.md`) are **not** in the diff —
      they should be gitignored

See [TEAM-WORKFLOW.md](../TEAM-WORKFLOW.md) for the full shared-repo workflow.
