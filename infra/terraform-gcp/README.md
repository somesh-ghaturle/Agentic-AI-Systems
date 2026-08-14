# GCP infrastructure

A parallel Terraform layout to `infra/terraform-aws` and `infra/terraform-azure`, enforcing
the same architecture on GCP primitives.

```
modules/   reusable modules — identity, security, state, archive, knowledge,
           model-integration, tools, approval, orchestration, observability
envs/      environment roots — dev, prod
tests/     static checks on the write boundary, no credentials required
```

**Start with [HOW-TO-DEPLOY.md](HOW-TO-DEPLOY.md).** It covers prerequisites, the two
manual pre-steps Terraform cannot perform, what prod does differently, and how to rehearse
the deny policy before trusting it.

---

## Status

`terraform validate` passes in both environments. `terraform plan` needs the deployment
packages built first — every function package path is read at plan time to compute a
deployment hash — so run `src/build.sh` before planning.

The handler source tree exists at `src/`. It is written against the Google Cloud SDKs
rather than ported line-by-line from `infra/terraform-aws/src`, because three things
genuinely differ:

- **Traces must go through the Logging API.** Anything a handler prints to stdout is
  captured automatically and appears in Cloud Logging looking perfectly healthy — in the
  function's own log, with no structured payload, where every metric filter misses it. The
  field is `event`, not `event_type` as on AWS and Azure, and the cost metric keys on a
  `terminal` flag rather than on the event name.
- **The approval claim needs a transaction.** DynamoDB expresses "update only if still
  pending" as a condition on one call; Firestore has no conditional update, so the
  equivalent is a transaction that reads, decides, and writes, and aborts if the document
  moved underneath it.
- **Packaging ships source, not wheels.** Cloud Build unpacks the zip and installs
  `requirements.txt` against the real runtime image, so vendoring wheels locally would
  shadow what it resolves correctly on its own. The runtime also preinstalls nothing beyond
  functions-framework, so every package declares its imports.

Every module described in
[ARCHITECTURE.md section 6](ARCHITECTURE.md#6--what-terraform-builds) is built.

---

## The one thing to understand before changing anything

Tools are split into `read` and `write`, and only the approval executor can invoke a write
tool. The orchestrator cannot — not "is not supposed to", but cannot.

Unlike the Azure tree, this is not a substitution for the AWS design; it is the same
mechanism. A Cloud Functions gen2 function is a Cloud Run service underneath, and a Cloud
Run service carries its own IAM policy. `roles/run.invoker` on that policy is the AWS
Lambda resource policy in different words.

GCP then adds a second lock that neither other tree has. An IAM Deny policy denies the
orchestrator the invoke permission on write tool services specifically. Deny rules evaluate
*before* allow policies, so this holds even if somebody later grants the orchestrator a
broad project-level `run.invoker` — the exact accident resource-scoped grants cannot
prevent.

Between them: remove either and the other still refuses.

### The mistake this tree is built to prevent

A gen2 function has no invoker binding of its own. Granting
`roles/cloudfunctions.invoker` on the function resource looks correct, appears in the
console, applies without error, and does not control HTTP invocation at all.

For a read tool that fails loudly — nothing works. For a write tool it fails silently in
the dangerous direction, because the tool is then invokable by anyone holding
`run.invoker` from any other grant.

`terraform validate` is perfectly happy: it is a valid role string in a valid attribute.
[`tests/test_write_boundary.py`](tests/test_write_boundary.py) is what catches it, along
with four other mistakes of the same shape — including deny policies written with
`serviceAccount:` principals, which GCP accepts and matches against nothing.

Those tests read `.tf` files as text, need no credentials, and run in CI.

---

## Why there is an `identity` module when AWS has none

The enforcement flow is circular: `modules/tools` needs the executor's identity to scope
its write-tool invoker binding, and the executor needs the write tools' addresses to call
them.

AWS breaks this by computing ARNs in `locals` — resource names are deterministic, so their
ARNs are known before the resources exist. GCP service account emails are deterministic
too, so the same trick would work here.

It is deliberately not used. Constructing an email produces a value that is correct and
*unverified*: GCP accepts an IAM binding naming a service account that does not exist,
without error. If the account is never created, or is created in another project, Terraform
is perfectly happy and the binding references a principal that isn't there — surfacing
later as a 403 that looks like a permissions bug.

Creating them up front and passing the resource through makes a typo a plan-time failure.

The env roots break the two remaining cycles the AWS way, with deterministic names: the
workflow name and the archive bucket name are both computed in `locals`. Both are annotated
at the top of `envs/dev/main.tf`.

---

## Credentials

There are none. No service account keys, no function keys, no secrets in environment
variables. Every workload runs as its own service account and GCP holds the credential.

`modules/security` can create a Secret Manager secret for a model API key, and it is off by
default rather than creating an empty secret nobody fills. Claude on Vertex AI
authenticates as the caller's service account, so in this tree there is no key to store.

If you find yourself adding a secret to make something work, that is the signal to check
what identity should have been granted instead.

---

## Claude on Vertex AI

`modules/model-integration` grants `roles/aiplatform.user` to the reason tool and enables
the API. It creates nothing else, because there is nothing else to create — Vertex AI
serves Anthropic models through a regional endpoint rather than through a provisioned
resource.

Two things it cannot do for you:

- **Accepting the Model Garden terms** for the model in the target project. There is no
  Terraform resource and no API. Without it every call returns 403.
- **Checking that `model_id` exists.** It is passed to handlers as an environment variable
  verbatim.

`vertex_location` is deliberately a separate variable from `region`. Anthropic model
availability on Vertex AI is region-specific and does not always include the region the
rest of the stack runs in; `us-east5` and `europe-west1` carry the broadest selection.

---

## Cost

The one thing here that bills continuously regardless of traffic is the Vector Search
deployed index. There is no scale-to-zero: `min_replica_count` is a standing bill, not a
ceiling. Dev runs one replica; prod runs two so a single replica restarting does not take
retrieval down.

Everything else is request-priced or near-free at rest. The `cost_usd` metric and its daily
alert cover model spend, which is the part that varies with how well the agent behaves —
in dev the threshold is set as a runaway-loop detector rather than as a budget.
