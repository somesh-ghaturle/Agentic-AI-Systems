---
description: How much supervision a task gets, decided before work starts
globs: ["**/*"]
---

# Autonomy rules

Autonomy is chosen **per task, before starting** — not globally, and not discovered
halfway through a review.

## The buckets

### Green — run it, review the diff at the end

Peripheral, reversible, and covered by existing tests.

- Writing or extending tests
- Documentation, comments, docstrings
- Scaffolding a new module from an existing pattern
- Mechanical refactors where the test suite is already green
- Logging, error messages, dev-only config
- Formatting and lint fixes

### Yellow — plan first, review each significant edit

Real logic, contained blast radius.

- Feature work in application code
- Internal APIs and their callers
- Data transforms and business rules
- Dependency upgrades (minor/patch)
- Performance work

### Red — step-by-step, every line read by a human, no auto-accept

Core, security-relevant, or hard to reverse.

- Authentication, authorization, session handling
- Cryptography, key handling, anything touching secrets
- Payments, billing, financial calculations
- Database migrations and any destructive data operation
- Production configuration and deploy pipelines
- Public API contracts and anything with external consumers
- Deletes of any kind: files, records, branches, resources

## Deciding, when it is not obvious

Ask in order — the first "yes" sets the bucket:

1. Could this lose data, money, or access if it is wrong? → **Red**
2. Would a subtle error here be invisible in testing and expensive in production? → **Red**
3. Does it touch a path listed under Boundaries in `CLAUDE.md`? → **Red**
4. Is it business logic a user depends on? → **Yellow**
5. Is it fully covered by tests that would catch a regression? → **Green**
6. Still unsure? → **Yellow.** Escalate on doubt, never de-escalate.

## Rules that hold in every bucket

- **State the bucket before starting.** One line: "Treating this as Yellow because it
  changes the pricing path."
- **Escalate mid-task when scope changes.** A Green refactor that turns out to touch auth
  becomes Red immediately — stop and say so rather than finishing.
- **Green is about supervision, not care.** Auto-accept means the human reviews at the end,
  not that quality is optional.
- **Never auto-accept a first-try success in Red.** Code that worked immediately in a
  sensitive area is the profile of a subtle bug, not of an easy problem.
