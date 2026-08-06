---
description: Domain rules for the payments subtree — example of a path-scoped rule
globs: ["src/payments/**", "tests/payments/**"]
---

# Example: a path-scoped rule

<!--
  THIS FILE IS AN EXAMPLE. Replace it with a real one, or delete it.

  The point of this file is the `globs:` line in the frontmatter above. Rules scoped to a
  path load only when the agent is working in that path. This is how you keep CLAUDE.md
  under 200 lines while still having deep, specific rules for the areas that need them.

  Rule of thumb: if a constraint only applies to one subtree, it belongs in a file like
  this, not in CLAUDE.md. If it applies everywhere, it belongs in CLAUDE.md.
-->

## When this applies

Any work under `src/payments/` or its tests.

## Domain invariants

These are correctness requirements, not style preferences. Violating one is a bug even if
all the tests pass.

- **Money is never a float.** Use integer minor units (cents) or `Decimal`. A `float`
  anywhere in a monetary path is a defect.
- **Currency travels with the amount.** No bare amounts crossing a function boundary — an
  amount without its currency is meaningless and will eventually be added to the wrong thing.
- **Every mutation is idempotent.** Requests carry an idempotency key; a retry must not
  double-charge.
- **Rounding is explicit at the boundary**, using the documented mode. Never let an
  implicit cast round for you.

## Required patterns

- All external calls go through `src/payments/gateway/` — never call the provider SDK
  directly from business logic.
- Every state transition is written to the ledger before the response is returned.
- Failures are typed (`PaymentDeclined`, `GatewayTimeout`, …), never a generic `Exception`.

## Testing requirements

- Every new path needs a test for: success, decline, timeout, and duplicate-retry.
- Use the fixtures in `tests/payments/fixtures/`. Do not invent new test cards.
- Never hit the live gateway from a test. If a test seems to need it, stop and ask.

## Autonomy

This subtree is **Red**. Plan first, no auto-accept, every line reviewed by a human.
See [autonomy.md](autonomy.md).
