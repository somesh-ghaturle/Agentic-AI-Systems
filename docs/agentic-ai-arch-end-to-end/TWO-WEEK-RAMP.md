# A concrete two-week ramp

The habits in [PLAYBOOK.md](PLAYBOOK.md) in the order that actually builds them. Roughly
30–60 minutes of deliberate setup, then normal work on top of it.

Pick **one real repository** — something you actively work on. A toy project will not
surface the friction that makes these habits necessary.

---

## Week 1 — Foundations

Goal: the agent has real context and an objective signal it can iterate against, and you
have run three real tasks plan-first.

### Day 1 — Context

- [ ] Copy [templates/root/CLAUDE.md](templates/root/CLAUDE.md) to your repo root
- [ ] Fill in: stack, the four commands, layout, conventions, boundaries
- [ ] **Verify every command actually runs** on a clean checkout — a wrong test command is
      worse than none, because it produces confident wrong verification
- [ ] Cut it to **under 200 lines**. Delete every line you would not enforce in review

> The whole file is optional except the commands. Without a runnable test command the agent
> cannot verify its own work, and Week 1 does not really start.

### Day 2 — Scoped rules

- [ ] `mkdir -p .claude/rules`
- [ ] Copy [verification.md](templates/.claude/rules/verification.md) and
      [autonomy.md](templates/.claude/rules/autonomy.md)
- [ ] Write **one** rule file for a real subdirectory, with a `globs:` line — use
      [example-scoped-rule.md](templates/.claude/rules/example-scoped-rule.md) as the shape
- [ ] Move anything subtree-specific out of `CLAUDE.md` and into it

### Day 3 — Make the signal real

- [ ] Get `<test>` running clean. If the suite is red, fix it or scope to a green subset —
      the agent needs an unambiguous signal, and a suite that is always red provides none
- [ ] Get lint and type check running clean
- [ ] If the project has no tests at all, **write the first one today**. That is the task

### Days 4–5 — Three real tasks, plan-first

- [ ] Copy the [worksheets](worksheets/) to your repo root
- [ ] Copy [plan.md](templates/.claude/commands/plan.md) and
      [verify.md](templates/.claude/commands/verify.md) into `.claude/commands/`
- [ ] Run **three real tasks**, each: `/plan` → read and correct the plan → execute →
      `/verify`
- [ ] Deliberately pick one Green, one Yellow, one Red so you feel the difference
- [ ] Use [checklists/task-start.md](checklists/task-start.md) before each

**End of Week 1 you should have:** a filled `CLAUDE.md`, two or three rules files, a green
verification command, and three tasks completed plan-first with real evidence.

---

## Week 2 — Instrumentation

Goal: stop retyping. Turn repetition into artifacts so next week is cheaper than this week.

### Day 6 — Two commands

- [ ] Look back at Week 1. **What did you type twice?** That is your first command
- [ ] Write two commands in `.claude/commands/` for your own repeated prompts
- [ ] Good candidates: your PR-prep sequence, your debugging opener, your release checks

### Day 7 — One skill

- [ ] Pick domain knowledge the agent keeps needing and cannot infer — an internal API's
      real behavior, a house format, a non-obvious domain rule
- [ ] Write it as a skill using [the template](templates/.claude/skills/example-skill/SKILL.md)
- [ ] Spend your effort on the `description` — it decides whether the skill ever fires

### Day 8 — One subagent

- [ ] Pick a research-heavy or noisy task that would flood your main context
- [ ] Write **one feature-specific** agent — see
      [the template](templates/.claude/agents/example-feature-agent.md)
- [ ] Name your real paths, fixtures, and commands in it. Resist writing a generic
      "QA agent"; specificity is the entire value

### Day 9 — Context hygiene

- [ ] Copy [handoff.md](templates/.claude/commands/handoff.md) into `.claude/commands/`
- [ ] Practice: work → `/handoff` → clear → resume from the files alone
- [ ] Read [checklists/context-hygiene.md](checklists/context-hygiene.md) and consciously
      catch yourself in one of the two failure modes this week

### Day 10 — Close the loop

- [ ] Fill in `learnings.md` from everything the agent got wrong over two weeks
- [ ] **Promote** the recurring ones into `CLAUDE.md` or a rules file
- [ ] Copy [review-diff.md](templates/.claude/commands/review-diff.md) and run it on a
      real diff
- [ ] Adopt [checklists/pre-merge.md](checklists/pre-merge.md) as your merge gate

**End of Week 2 you should have:** two commands, one skill, one subagent, a handoff habit,
and a `learnings.md` that has already fed back into your rules at least once.

---

## Week 3 and beyond — extend past code

The largest wins reported inside Anthropic came from people automating workflows nobody
classified as engineering: lawyers building phone-tree systems, marketers generating
hundreds of ad variations, data scientists building visualizations without knowing
JavaScript.

Look for the same shape in your own week — repetitive, rule-shaped, currently manual:

- Incident runbooks and post-mortem drafting
- Recurring report generation
- Data pulls and reconciliations
- Migration and upgrade sweeps across many files
- Onboarding docs that go stale
- Compliance evidence collection

The habits transfer unchanged. The context file describes the domain instead of the stack;
the verification signal is a script that asserts the output instead of a test suite.

---

## Signals you are actually improving

| Week 0 | Week 4 |
|---|---|
| "Should work" | Pasted test output |
| One giant session per day | One session per task |
| Retyping the same prompt | `/command` |
| "The model is dumber today" | "My context is polluted, clearing" |
| Reviewing summaries | Reviewing diffs |
| Same mistake every week | It is in the rules file now |

## Signals you are stuck at habit 1

Most people plateau here. The tells:

- No `CLAUDE.md`, or one nobody has edited since it was generated
- No `.claude/commands/` directory at all
- Cannot name the test command from memory
- Every session starts by re-explaining the project

The fix is Day 1 of Week 1. It is genuinely about an hour of work.
