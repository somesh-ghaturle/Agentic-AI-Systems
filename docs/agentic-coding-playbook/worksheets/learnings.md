<!--
  Copy to your repo root as learnings.md.

  This is the file that makes the whole system compound. Every time the agent gets
  something wrong, write it here. Every week, promote the recurring ones into CLAUDE.md
  or a .claude/rules/*.md file.

  Without this step, you correct the same three mistakes forever and plateau. With it,
  each mistake is paid for once.
-->

# Learnings

Append-only. Newest at the top.

---

## `<YYYY-MM-DD>` — `<short title>`

**What it got wrong:** <the mistake, concretely>

**Why:** <the missing context, ambiguous rule, or wrong assumption behind it>

**Correction:** `<what the right behavior is>`

**Promote to:** `CLAUDE.md` | `.claude/rules/<file>.md` | a command | nowhere, one-off
**Promoted:** ☐ not yet | ☑ done `<date>`

---

## Example entry — delete this

**2026-01-15 — Invented a new HTTP client instead of using the existing one**

**What it got wrong:** Added `httpx` directly in a new service module and built a fresh
retry wrapper, when `src/clients/base.py` already provides a configured client with
retries, timeouts, and tracing.

**Why:** Nothing told it the shared client existed. It reasonably solved the problem it
could see from the files it had read.

**Correction:** All outbound HTTP goes through `src/clients/base.py`. Never instantiate a
raw client in a service module.

**Promote to:** `CLAUDE.md` → Conventions
**Promoted:** ☑ done 2026-01-15

---

## Promotion review

Do this weekly. It takes five minutes and it is where the compounding actually happens.

- [ ] Anything appearing **twice** → promote to a rules file immediately
- [ ] Anything scoped to one subtree → `.claude/rules/*.md` with a `globs:` line, not `CLAUDE.md`
- [ ] Anything you have now prompted twice → make it a command
- [ ] `CLAUDE.md` still under ~200 lines? If not, push detail down into scoped rules
- [ ] Any rule that is no longer true → **delete it**; stale rules cost the same as good
      ones and actively mislead

## Patterns worth watching

If the same *kind* of mistake keeps appearing, the fix is usually structural rather than
another rule line:

| Pattern | Likely real cause |
|---|---|
| Keeps missing existing helpers | Layout and conventions underspecified in `CLAUDE.md` |
| Keeps marking unverified work done | No runnable test command, or no verification rule |
| Keeps touching out-of-scope files | Boundaries section missing or too vague |
| Keeps suppressing errors | Missing the "fix root cause" rule |
| Quality drops mid-session | Context hygiene, not rules — see the hygiene checklist |
