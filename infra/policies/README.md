# Policies

Conftest/OPA policies over the Terraform source of all four cloud/data-platform trees. Run in
CI by the `conftest` job in [`checks.yml`](../../.github/workflows/checks.yml).

## What lives here, and what does not

Three tools scan `infra/`, and they answer different questions. Adding a check to the wrong
one buys a second opinion nobody reads.

| Tool | Question it answers | Where it is configured |
|---|---|---|
| [tflint](../../.tflint.hcl) | Is this valid, idiomatic Terraform? | `.tflint.hcl` |
| [checkov](../../.checkov.yaml) | Is this resource configured safely? | `.checkov.yaml` |
| **conftest** | **Do the resources agree with each other?** | this directory |

checkov asks whether a guardrail is configured well. It does not ask whether anything points
at it, because that is a question about a *pair* of resources and checkov evaluates one at a
time. The write-boundary suites under `infra/*/tests/` do reason across resources, but they
are per-tree Python reading `.tf` as text, and they cover a different control.

The gap conftest fills is **declared but not wired**: a resource that exists, reads as a
control, and has nothing referencing it. That defect is invisible in a plan diff — adding the
guardrail and forgetting the reference both show up as resources created.

A check belongs here when it is about a relationship between resources. A check about a single
resource's attributes belongs in checkov, where the rule already exists and is maintained.

## Policies

- **[`guardrail_wiring.rego`](guardrail_wiring.rego)** — every content filter must be attached
  to the thing it filters. Each tree wires this differently, which is deliberate (see
  [ADR 0002](../../docs/DECISION-LOGS/0002-azure-openai-vs-claude.md)): AWS through
  `aws_bedrock_guardrail_version`, Azure through `azurerm_cognitive_deployment.rai_policy_name`,
  GCP through `google_model_armor_floorsetting`. One invariant, three primitives, one file —
  three copied files would drift.
- **[`lib.rego`](lib.rego)** — shared accessors over conftest's HCL2 parse tree.

## Running it

```bash
# The policies' own unit tests — run these first.
conftest verify --policy infra/policies

# The policies against one tree.
find infra/terraform-aws -name '*.tf' -not -path '*/.terraform/*' -print0 \
  | xargs -0 conftest test --parser hcl2 --combine --policy infra/policies
```

Two details in that command are load-bearing:

- **`--combine`** merges every file into one document before evaluating. Without it each file
  is judged alone, and a guardrail declared in `main.tf` and wired in `deployment.tf` reads as
  unwired. Under `--combine`, `input` is an array of `{path, contents}` — which is the shape
  the tests in [`guardrail_wiring_test.rego`](guardrail_wiring_test.rego) mock.
- **The `find` pipeline** rather than a directory argument. `--parser hcl2` forces every file
  it is handed through the HCL parser, so pointing it at `infra/terraform-aws/` makes it try to
  parse `.gitignore` and fail. Naming the `.tf` files is narrower than an ignore regex and
  needs no editing the next time a new file type lands under `infra/`.

## Source, not plan output

These policies read Terraform **source**, not `terraform show -json` plan output, which is the
more common way to run OPA against Terraform.

That is a deliberate constraint, not a limitation to fix later. `checks.yml` states it in its
own header: *"Everything here runs without cloud credentials."* Plan JSON requires
`terraform plan`, which contacts the provider and needs credentials — the reason
[enhancement task 6](../../docs/ENHANCEMENT-PLAN.md) is filed as Blocked rather than pending.
Writing these against plan output would have imported that blocker.

The cost is real and worth stating: source parsing sees the expression, not the resolved value.
`rai_policy_name` arrives as the literal string
`${var.create_content_filter ? azurerm_...guardrail[0].name : null}`, so wiring is checked by
substring — a reference that appears anywhere in the expression counts as a reference. That
catches the deletion these policies exist to catch. It would not catch a reference guarded by a
condition that is always false.

## Adding a policy

Write the rule and its tests in the same change. `conftest verify` runs first in CI precisely
because a policy that cannot fail passes every tree it is pointed at, which looks identical to
a policy that holds. Each rule gets both directions asserted: silent on correct config, firing
on config missing exactly the thing the rule is about.
