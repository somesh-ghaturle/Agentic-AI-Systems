# Pre-apply checklist

Run before the first prod apply, and again whenever the tool set or the approval flow
changes. Most of these are cheap to check now and expensive to discover later.

---

## Decisions that cannot be undone

- [ ] **Object Lock** — decided? S3 cannot enable it on an existing bucket, and COMPLIANCE
      mode cannot be shortened by anyone, including the root account
- [ ] **`project` name** — final? Renaming recreates every resource
- [ ] **Region** — final? Everything here is regional
- [ ] **Archive retention** — from your records policy, not from the default

## State

- [ ] Remote backend configured and the `backend "s3"` block uncommented
- [ ] State bucket has versioning enabled
- [ ] Lock table exists
- [ ] `terraform.tfvars` is **not** committed

## Handler code

The reference handlers in [src/](../src/README.md) leave three functions raising
`NotImplementedError`, each at a point where a working default would be dangerous. None of
them can reach prod as they stand.

- [ ] `_resource_owner` in `approval_validator/validator.py` points at your system of
      record, and the validator role has read access to it
- [ ] `_submit_refund` in `process_refund/index.py` calls the real provider and passes
      `idempotency_key` as the provider's idempotency header
- [ ] `EMBEDDING_MODEL_ID` is set and the retrieve role has `bedrock:InvokeModel` for it
- [ ] `REQUIRED_ROLES` in the validator lists every approvable action — an action missing
      from that map is refused, which is the intended default for a newly added write tool
- [ ] `python3 -m unittest discover -s tests` passes from `src/`
- [ ] `./build.sh` has been run since the last handler change — Terraform hashes the zip,
      not the source

## The read/write split

This is the property everything else rests on. Check it deliberately.

- [ ] Every tool's `access` reflects **what the handler does**, not what it is named
- [ ] No tool marked `read` mutates state, writes an audit row, or sends a message
- [ ] `terraform output write_tools` lists everything irreversible, money-moving,
      customer-data-touching, externally-visible, or code-executing
- [ ] After apply: `aws lambda get-policy` on each write tool names the **approval
      executor** as principal, not `states.amazonaws.com`

## Approval gate

- [ ] State machine type is `STANDARD` (the module checks this, but confirm you did not
      override it)
- [ ] The validator checks ownership, permissions, and limits **in code** — not in a prompt
- [ ] Approval notifications carry what, to whom, why, and the effect. "Execute tool
      `process_refund`?" is a rubber stamp with extra steps
- [ ] SNS subscriptions exist and are **confirmed** — an unconfirmed subscription silently
      drops messages and executions sit until timeout
- [ ] Approval timeout is short enough that a stale approval fails rather than executing
      against changed state
- [ ] Someone is actually on the receiving end, and knows they are

## Reliability

- [ ] Every tool has a timeout (the module enforces this)
- [ ] The state machine has `TimeoutSeconds`
- [ ] The loop is bounded — a step counter checked against a maximum
- [ ] Every task state has `Retry` with backoff and jitter, and a `Catch`
- [ ] Retries are capped
- [ ] Write handlers are **idempotent on a key** — agents retry, and retries must not
      double-charge
- [ ] Failure paths are designed for each step: malformed output, tool timeout, empty
      retrieval, abandoned approval, mid-workflow restart

## Security and privacy

- [ ] Knowledge collection is **not** public (`allow_public_access = false` in prod)
- [ ] PII is masked **before** it reaches the model, in application code
- [ ] Indirect PII paths considered: stack traces, error messages, tool outputs, retrieved
      documents
- [ ] `log_execution_data = false` in prod, or payloads are provably masked
- [ ] Retrieval applies **metadata filtering before semantic search** — this is what
      prevents cross-tenant leakage
- [ ] Retrieved content cannot directly trigger a write
- [ ] Each tool role has only the permissions that tool needs
- [ ] Third-party MCP servers or tool packages vetted like CI plugins — they run with your
      agent's permissions

## Observability

- [ ] Handlers emit the trace schema in `modules/observability/outputs.tf` — the metric
      filters match nothing otherwise
- [ ] Traces go to the **shared** trace log group, not each function's `/aws/lambda` group.
      The filters are attached to one group; a handler logging to its own is invisible to
      every alarm while looking perfectly healthy in the console
- [ ] `trace_emitter` is set. The orchestrator's own records — terminal outcomes, the loop
      bound firing — cannot reach the trace group without it, and the loop-bound and cost
      alarms then sit at zero indefinitely
- [ ] The model step returns `usage` with `total_tokens` and `cost_usd`. The terminal
      record carries what the model reports and nothing is inferred, so no usage means no
      cost metric and a daily-cost alarm that can never fire
- [ ] `correlation_id` threads through every step
- [ ] `model_version` and `prompt_version` are recorded; results are not reproducible
      without them
- [ ] `cost_usd` and `total_tokens` on the terminal record only, not per step
- [ ] `alarm_topic_arns` is non-empty and someone receives it
- [ ] `daily_cost_threshold_usd` set from observed spend plus headroom

## Cost

- [ ] OpenSearch Serverless minimum OCU understood — it bills continuously, with or
      without traffic, and dominates a quiet environment's bill
- [ ] `reserved_concurrency` bounds write tools
- [ ] Token limits enforced per step and per request, in application code
- [ ] Model routing considered — a frontier model on every step, including intent
      classification, is the most common avoidable cost

## Governance

Only if you are in a regulated environment — see
[ENTERPRISE-ADAPTATION.md](../../../docs/agentic-coding-playbook/ENTERPRISE-ADAPTATION.md).

- [ ] Model, hosting, and data-retention position approved
- [ ] Data classification tagged and correct
- [ ] Audit evidence retained: which model, which prompt version, who approved, what
      happened
- [ ] Approval log retention meets your policy
- [ ] Change-management path for agent-initiated actions agreed

---

## After apply

Evidence, not "should work":

- [ ] `terraform output write_tools` matches what you expect
- [ ] `aws lambda get-policy` on a write tool shows the executor as principal
- [ ] A test execution proposing a write **blocks** in `RUNNING` rather than completing
- [ ] Approving it executes; denying it records a rejection
- [ ] A trace appears in **the trace log group** — `/agentic/<prefix>/traces`, not the
      function's own group — with the full field set
- [ ] An execution driven past its step budget produces a `loop_bound_exceeded` record
      there, and the loop-bound alarm leaves INSUFFICIENT_DATA
- [ ] An alarm fires when deliberately tripped
