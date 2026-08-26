# ADR 0003 — Two Firestore databases on GCP, not one Spanner instance

**Status: Accepted** · Decided 2026-08-12 · Scope: `infra/terraform-gcp/`

> **On the title.** Spanner appears nowhere in this tree and never did. This record exists to
> say why it was not reached for, and to capture the half of the decision that matters more in
> practice: GCP runs **two** Firestore databases with **different concurrency modes**, and a
> Firestore transaction is the approval-claim primitive.

## Context

Every tree needs two stores with genuinely different properties:

- **Execution state** — operational, per-execution, regenerable by running the thing again.
- **Approval records** — the evidence of who authorized what. They outlive the execution that
  produced them, and they are also the concurrency control that stops an approval being
  claimed twice.

GCP allows multiple named Firestore databases per project, which is what makes separating them
cheap here. On AWS it is two DynamoDB tables; on Azure a Storage Table and a Cosmos container.

The approval claim is the other constraint. The executor must claim a record exactly once under
Pub/Sub redelivery. Each cloud spells the same invariant differently — DynamoDB condition
expression, Cosmos ETag with `if_match`, Firestore transaction
([`src/shared/firestore_io.py`](../../infra/terraform-gcp/src/shared/firestore_io.py)).

## Decision

Firestore Native, two databases, different concurrency modes:

| Database | Mode | Why |
|---|---|---|
| `<prefix>-state` ([`modules/state/main.tf`](../../infra/terraform-gcp/modules/state/main.tf)) | `OPTIMISTIC` | One document per execution; the orchestrator does not contend with itself, so pessimistic buys nothing and costs latency. |
| `<prefix>-approvals` ([`modules/approval/main.tf`](../../infra/terraform-gcp/modules/approval/main.tf)) | `PESSIMISTIC` | The claim is a read-then-conditional-write, and two executors racing on a redelivered Pub/Sub message is the case that matters. |

## Consequences

- **No provisioned capacity, which is the main reason.** Firestore bills per operation and per
  byte stored, so an idle environment costs roughly what it is storing. Spanner's smallest unit
  is provisioned compute that bills whether or not anything calls it. This tree already carries
  one standing cost that cannot be scaled to zero — Vertex AI Vector Search in
  `modules/knowledge` — and did not want a second in a reference deployment people are meant to
  destroy and rebuild.
- **Query planning becomes a Terraform concern.** Firestore requires a composite index for any
  query combining an equality filter with an ordering on a different field, and the failure mode
  is a runtime error carrying a console link rather than anything Terraform catches. Hence
  `google_firestore_index.executions_by_status`, which exists so that "what is still running"
  and "what failed in the last hour" work the first time.
- **Database IDs are immutable.** Renaming means creating a new database and losing everything
  in the old one. Names derive from `name_prefix`, which makes `name_prefix` effectively
  immutable too, in a way `terraform plan` will happily show as a replacement.
- **Two delete protections that read as one.** `delete_protection_state` governs what the API
  permits; `deletion_policy` governs what Terraform does. Prod sets both, which is why a prod
  teardown takes two steps — the intended amount of friction.
- No SQL, no joins, no strongly consistent secondary indexes across databases. Anything that
  wants a relational read of execution state against approvals reads both and joins in the
  handler.

## Alternatives considered

1. **Spanner.** The strongest consistency story on GCP and real SQL, and it would collapse both
   databases into one instance with two tables. Rejected on standing cost: there is no
   scale-to-zero, so every dev and staging environment would bill continuously for compute that
   is idle almost all of the time.
2. **Cloud SQL.** Cheaper than Spanner and still an always-on instance, plus connection
   management from Cloud Functions — a pool per instance, against a database with a connection
   limit. Rejected for the same standing-cost reason and one extra failure mode.
3. **One Firestore database with two collections.** The cheapest thing to build, and wrong for
   the reason the module comments give: execution state and approval evidence have different
   retention needs, different readers, and different consequences when lost. It would also force
   one concurrency mode onto two workloads that want opposite ones.

## What would reopen this

Execution state growing a genuinely relational query pattern, or an environment needing
cross-region strong consistency. Either is a real reason to look at Spanner again; neither is
true of this tree today.
