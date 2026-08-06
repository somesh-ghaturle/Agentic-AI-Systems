# Context hygiene checklist

Two failure modes, named so you catch them **while they are happening** rather than after
you have burned an hour.

---

## Failure mode 1 — the kitchen-sink session

**What it looks like:** you debugged a flaky test, then pivoted to a UI change, then asked
about deployment, all in one context. Answers are getting vaguer. Suggestions reference the
earlier task. It "feels dumber than this morning."

**What is happening:** unrelated earlier material is still in context and still being
attended to. It distorts later reasoning. This is reliably misdiagnosed as model
degradation — it is not, and no prompt improvement fixes it.

**Catch it with:**

- [ ] Is everything in this session about **one task**?
- [ ] If I described this session in one sentence, would it need the word "and"?
- [ ] Have I pivoted topics since the last clear?

**Fix:** `/handoff`, clear, restart with only the current task.

---

## Failure mode 2 — correcting in circles

**What it looks like:** attempt fails, you correct, it fails differently, you correct again.
Third correction. The fixes are getting narrower and the progress is asymptoting.

**What is happening:** every failed attempt is still in context. The model is now reasoning
inside a neighborhood defined by four wrong approaches, and each correction anchors it
further rather than freeing it.

**Catch it with:**

- [ ] Have I corrected the **same thing** twice?
- [ ] Are the last three exchanges shorter and more specific than the three before?
- [ ] Am I fixing the fix rather than the problem?

**Fix — do not correct a third time:**

1. Write down what it keeps getting wrong, in `learnings.md`
2. Save real progress to `plan.md` / `context.md`
3. **Clear the context**
4. Restart with a sharper prompt that states the constraint up front — the thing you have
   now explained three times goes in the *first* message, not the fourth

---

## Routine hygiene

**Clear between tasks.** One session, one task. Clearing is cheap; a polluted context is
not.

**Handoff before compaction.** When context is getting long, run `/handoff` first so state
lives in files rather than depending on what survives summarization.

**Point, do not paste.** Say "read `src/checkout/promos.py`" instead of pasting the file.
The agent reads what it needs; you avoid paying for the whole file every turn.

**Subagent the noisy work.** Research and broad searches produce large intermediate output.
Run them in a subagent so only the conclusion lands in your main context.

**Prune your own rules.** A `CLAUDE.md` that has grown past ~200 lines is costing you on
every single turn, forever. Push the specific parts into path-scoped
`.claude/rules/*.md` and delete anything you would not actually enforce.

---

## The tell

> When output quality drops mid-session, the first hypothesis should be **"my context is
> polluted,"** not "the model is having a bad day."

The first one is true far more often, and unlike the second it has a fix you can apply in
about ten seconds.
