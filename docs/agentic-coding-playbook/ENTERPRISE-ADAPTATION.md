# Enterprise adaptation

For regulated environments — banks, insurers, healthcare, government, anywhere with a
model-risk function.

## The short version

**The habits transfer cleanly. The "point it at prod and let it run" parts do not.**

Nothing in [PLAYBOOK.md](PLAYBOOK.md) conflicts with governance. Thin context, plan-first,
verification-in-the-loop, per-task autonomy, and human review are *strengthened* by a
control environment, not opposed by it — several of them are controls you would have to
invent anyway.

What changes is that three things become governed rather than personal choices:

1. **Tool access** — what the agent may run, read, and reach
2. **Data egress** — what leaves your boundary, and to where
3. **Model provenance** — which model, hosted where, under what terms, with what retention

Worth asking about in your **first week** rather than discovering later. The uncomfortable
version of this conversation is the one that happens after code is already written.

> **Security is its own document.** Prompt injection, secrets handling, supply chain, and
> IP/licensing are covered in [AGENT-SECURITY.md](AGENT-SECURITY.md), written to be read
> standalone by a security reviewer. This document covers governance and rollout.

---

## Questions to ask early

Bring these to your platform, security, or model-risk contact. Answers determine what your
setup can look like.

**Model and hosting**
- Which models are approved, and through which endpoint — vendor API, a cloud provider's
  hosted version, or an internal gateway?
- What is the data retention and training-use position on that endpoint?
- Is there an approved-tools list, and is the agent CLI on it?

**Data boundaries**
- May source code leave the network boundary? All of it, or by classification?
- What about logs, stack traces, config, schema, and test fixtures? These leak more than
  people expect — a stack trace can carry customer data.
- Are there repositories or paths that must never be in an agent's context?

**Execution**
- May the agent execute shell commands? Which ones?
- May it reach the network from the dev environment?
- May it touch non-production databases? Which environments are in scope at all?

**Change management**
- How is agent-assisted code identified in review — a commit trailer, a PR label?
- Does it require a different review threshold?
- What evidence must be retained to show a human reviewed it?

---

## What tightens

### Autonomy shifts toward Red

The bucket definitions in [autonomy.md](templates/.claude/rules/autonomy.md) hold, but the
membership changes. In a regulated environment, treat as **Red** by default:

- Anything touching customer data, PII, or PHI
- Anything in a system of record
- Anything with a regulatory reporting dependency
- Anything in scope for SOX, PCI-DSS, HIPAA, or equivalent
- Anything that changes an audit trail
- Model-serving code subject to model-risk management

Auto-accept generally survives for tests, docs, and internal tooling. That is still real
leverage — most of the volume is there.

### Boundaries become mandatory, not advisory

The Boundaries section of `CLAUDE.md` stops being a convenience and becomes a control. It
should name, explicitly:

- Paths the agent must never read (credentials, key material, production config)
- Paths it must never write (audit logs, migrations, IaC, pipeline definitions)
- Data it must never place into context (real customer records — use synthetic fixtures)
- Commands it must never run (anything touching prod, anything destructive)

Where the platform supports enforcement — permission settings, hooks, allowlists — enforce
it there too. A rule in a markdown file is guidance; a denied tool call is a control.

### Verification gains an audit dimension

Beyond "does it work," you now need "can we show it was checked." Retain:

- Which model and version produced the change
- The plan that was reviewed, and by whom
- Test output as evidence, not just as a signal
- The human reviewer, on the record

Much of this falls out of the playbook naturally — `plan.md` reviewed before execution is
already a documented control point, and pasted test output is already evidence. Point that
out when the control conversation happens; you are usually further along than it appears.

---

## What stays exactly the same

- Thin, deliberate context
- Plan first, execute second
- Verification in the loop, fix root causes
- One session, one task
- Prompted twice → artifact
- Read diffs, not summaries

None of these require any permission from anyone. Build them now, regardless of where the
governance conversation lands.

---

## Cost, and who pays for it

Token spend is invisible until it is a line item someone has to defend. Get ahead of it.

**What actually drives cost.** Not the number of people — the shape of their sessions. A
long-running session re-sends its accumulated context on every turn, so a polluted
five-hour session costs far more than five clean one-hour ones. Context hygiene is a cost
control before it is a quality control, which is a useful thing to mention when the
finance conversation happens.

**Set up attribution before you need it.** Per-team or per-project keys, so spend maps to
a budget owner. Retrofitting attribution after three months of pooled usage is unpleasant.

**Expect the distribution to be lopsided.** A small number of people will account for most
of the spend, and they are usually the ones getting the most value. Investigate before
capping — the useful question is whether their pattern should be taught to everyone, not
whether it should be stopped.

**Compare against the right baseline.** The comparison finance will reach for is "cost per
seat versus zero." The honest comparison is against engineering hours saved, and against
the review time you now spend instead. Both directions are real; present both.

**Practical controls:** budget alerts rather than hard caps at first, since a hard cap
mid-task wastes the work already paid for. Prompt caching where the platform supports it,
which mostly rewards the same thin-context discipline the playbook already asks for.

---

## Scale: config for hundreds of engineers

Everything in [TEAM-WORKFLOW.md](TEAM-WORKFLOW.md) holds. Three things change past roughly
fifty people.

**Layer the config deliberately.** Context files compose across org settings, user home
directory, project root, and subdirectories. Use that structure rather than fighting it:

| Layer | Owns | Changes |
|---|---|---|
| Org / enterprise settings | Security, compliance, and egress constraints | Rarely, through a governance process |
| Repository `CLAUDE.md` | Stack, commands, boundaries, conventions | Via PR, reviewed by the repo's owners |
| Subdirectory rules | Domain invariants for that subtree | Via PR, reviewed by the domain owner |
| Personal `~/.claude/CLAUDE.md` | Individual preferences | Freely, by the individual |

The failure mode is org-level rules that should have been repository-level: they apply
everywhere, cannot be tuned by the teams they affect, and get quietly worked around.

**Give rules an owner.** A rules file with no owner rots — it accumulates rules nobody
enforces and keeps rules whose reason expired. `CODEOWNERS` on `.claude/` and `CLAUDE.md`
is a small change that makes review routing automatic.

**In a monorepo, scope by path from day one.** A single root `CLAUDE.md` for a monorepo is
either uselessly generic or enormous. Push almost everything into path-scoped rules and
keep the root file to what is genuinely universal — the build system, the boundaries, the
commands.

**Do not centralize prompt libraries prematurely.** Teams sharing commands is good; a
central "approved prompts" repository that requires a ticket to change is a way to ensure
nobody writes commands at all. The whole value of habit 6 is that the loop from "I typed
this twice" to "it is a command" stays short.

---

## Legacy codebases with no verification signal

The playbook assumes a runnable test command. Large organizations frequently have
codebases where that assumption fails — no tests, a forty-minute build, a suite that has
been red for two years, or a system nobody fully understands.

**This is the honest hard case, and it is often where the leverage is.** The advice is not
"fix your test suite first," because that is a multi-year program.

**Build a narrow signal instead of a complete one.** You do not need the suite green. You
need *something* unambiguous for the code path you are touching:

- A characterization test that captures current behavior, whatever it is — not correct
  behavior, just present behavior, so you can detect change
- A script that exercises one path and asserts the output
- A diff of logs or output before and after
- For a UI, a screenshot comparison

Any of these is enough to iterate against, and writing one **is** the first task. That is
the same rule as everywhere else in the playbook; it just costs more here.

**Use the agent for comprehension, not only for change.** Explaining an unfamiliar
subsystem, mapping call paths, and drafting the characterization tests are all high-value
and low-risk — the output is a document or a test, and both are cheap to verify. Many
teams find this is where most of the value lands in a legacy system, well before any
production code changes.

**Autonomy skews Red by default.** In a system where the behavior is not specified and the
tests do not cover it, you cannot distinguish a bug fix from a behavior change. Treat that
as Red until characterization tests exist.

**Slow builds change the loop, not the habits.** When the signal takes forty minutes, the
plan-first discipline matters more, not less — you cannot afford to iterate blindly. Batch
verification, and use whatever fast partial signal exists (compile, lint, a subset) during
the loop.

---

## Offboarding and access changes

Rarely considered until an audit asks. The checklist is short.

- **Revoke API access** with everything else — the agent endpoint belongs on the standard
  offboarding list, and often is not on it yet
- **Personal config leaves with the person.** `~/.claude/` is theirs. Anything the team
  needs should already be in the repository, which is the practical argument for the
  shared/personal split
- **Review their recent agent-assisted changes** at the same bar as any other departing
  engineer's work
- **Rotate anything their agent had in scope** if credentials were ever in its
  environment. See [AGENT-SECURITY.md](AGENT-SECURITY.md)
- **Keep their learnings file.** `docs/learnings/<name>.md` is institutional knowledge and
  should outlive their access

---

## A workable rollout shape

1. **Start in the safest bucket.** Tests, docs, internal tooling, and non-production
   repositories. Real leverage, minimal control surface.
2. **Instrument before expanding.** Get `CLAUDE.md`, rules, and verification working where
   it is easy, so you can show a controlled setup rather than propose one.
3. **Bring evidence to the governance conversation.** "Here is our context file, our
   boundaries, our verification gate, and our review checkpoint" lands very differently
   from "can we use AI."
4. **Expand by classification, not by enthusiasm.** One data classification at a time, with
   the control questions answered for each.
5. **Keep `learnings.md` shared.** In an enterprise this doubles as the artifact that shows
   the practice is managed and improving.

---

## When agent-assisted code causes an incident

It will eventually, the same way human-written code does. What matters is that your process
does not treat it as a special category requiring a new investigation style.

**Run your normal incident process.** The change went through review and was approved by a
human — it is your organization's change, and the postmortem is about the same things it
always is: what broke, why the checks did not catch it, and what control closes the gap.

**Resist two opposite failure modes.** Blaming the tool and exempting the tool are both
wrong. "The AI wrote it" is not a root cause; neither is treating an agent-assisted defect
as unremarkable when the review process clearly did not fit the risk.

**The useful questions are about the process:**

- What autonomy bucket was this, and was that the right call in hindsight?
- Did the change have a verification signal, and did the signal cover the failure mode?
- Did a human read the diff, or approve a summary?
- Was this a conceptual bug that passed green tests — the known dominant class? If so, the
  gap is in review depth, not in testing volume
- Would any rule already in `CLAUDE.md` have prevented it, and was it followed?

**Close the loop structurally.** The finding goes into `learnings.md`, and anything
recurring gets promoted into a rule. An incident that changes no rule is one you have
agreed to have again.

For security incidents specifically — credential exposure, suspected injection, config
tampering — see [AGENT-SECURITY.md](AGENT-SECURITY.md). For the general process, see the
[incident runbook](../incident-runbook.md).

---

## Related material in this repository

The governance and security work here composes with this playbook:

- [Governance checklist](../governance-checklist.md)
- [Security checklist](../security-checklist.md)
- [Privacy checklist](../privacy-checklist.md)
- [Model card template](../model-card-template.md)
- [Datasheet template](../datasheet-template.md)
- [Incident runbook](../incident-runbook.md)

External frameworks worth citing in a control conversation:

- NIST AI Risk Management Framework — https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf
- EU AI Act — https://commission.europa.eu/publications/eu-artificial-intelligence-act_en
- OWASP Top 10 for LLM Applications — https://owasp.org/www-project-top-10-for-large-language-model-applications/
