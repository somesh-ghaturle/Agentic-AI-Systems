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

> Worth asking about in your **first week** rather than discovering later. The
> uncomfortable version of this conversation is the one that happens after code is already
> written.

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
