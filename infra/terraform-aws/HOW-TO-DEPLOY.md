# How to deploy

A walkthrough from an empty AWS account to a working dev environment, then what changes
for prod. Roughly an hour for dev if the handler code already exists.

---

## Before you start

**Required:**

- Terraform ≥ 1.6 (`optional()` in object types and `lifecycle.precondition` on resources)
- AWS credentials with permission to create IAM roles, Lambda, Step Functions, DynamoDB,
  S3, OpenSearch Serverless, KMS, SNS, and CloudWatch
- An S3 bucket and DynamoDB table for remote state (see below)

**Decide before the first apply,** because these cannot be changed without recreating
resources:

| Decision | Where | Why it is one-way |
|---|---|---|
| Object Lock on the archive | `archive_object_lock_days` | S3 cannot enable it on an existing bucket |
| `project` name | `project` | Renaming recreates every resource |
| Region | `region` | Everything is regional |

---

## 1 · Remote state

Local state for shared infrastructure means two people applying at once corrupt each
other's work. Set this up first:

```bash
aws s3api create-bucket --bucket my-tf-state --region us-east-1
aws s3api put-bucket-versioning --bucket my-tf-state \
  --versioning-configuration Status=Enabled

aws dynamodb create-table --table-name my-tf-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

Then uncomment the `backend "s3"` block in `envs/dev/main.tf` and fill it in.

---

## 2 · Build the handler packages

Terraform reads the zips at **plan** time via `filebase64sha256`, so they must exist
before you plan.

```bash
cd src
python3 -m unittest discover -s tests   # no AWS, no dependencies
./build.sh                              # writes ../build/*.zip
```

The reference handlers are in [src/](src/README.md) and they deploy as they stand, with
three deliberate exceptions. Ownership lookup, the payment call, and the embedding model
raise rather than guess, because each is a place where a plausible default is worse than a
failure. [src/README.md](src/README.md) lists them.

What each handler must do — including the parts the reference leaves to you — is in
[section 5](#5--what-the-handlers-must-do).

---

## 3 · Configure

```bash
cd envs/dev
cp terraform.tfvars.example terraform.tfvars
```

Fill in `project`, then the tools. **The `access` field is the one to get right:**

```hcl
tools = {
  lookup_order = {
    access          = "read"   # orchestrator invokes directly
    timeout_seconds = 30
    # ...
  }

  process_refund = {
    access          = "write"  # ONLY the approval executor can invoke
    timeout_seconds = 60
    # ...
  }
}
```

Classify by **what the handler does**, not by its name. A tool called `lookup_account`
that also writes an audit row is a write tool. When unsure, classify as `write` — an
unnecessary gate costs a click, a missing one costs an irreversible action nobody
authorized.

### The model step

The state machine's `Reason` state is the model call, and the reference ships no handler
for it — what you send a model and how you parse the response is the part of this system
that is actually yours. Declare it as a read tool named `reason` and the definition wires
itself:

```hcl
reason = {
  access          = "read"
  handler         = "index.handler"
  runtime         = "python3.12"
  package_path    = "../../build/reason.zip"
  timeout_seconds = 120
}
```

Two things it must return, because states downstream read them by path:

- `action_type` — `"write"` routes into the approval gate, `"continue"` loops, anything
  else completes
- `usage` — `{"total_tokens": …, "cost_usd": …}`, which is where the terminal trace record
  gets the numbers the cost alarm counts. No usage, no cost metric; the reference does not
  invent one

Leave `reason` undeclared and the definition renders with `REASON_TOOL_NOT_CONFIGURED` in
place of the ARN. The state machine still deploys, and fails at that step — visibly,
down the `RecordFailure` path, rather than silently.

### The state machine definition

`envs/*/state-machine.json.tftpl` is rendered by `templatefile` with the ARNs of things
that only exist after apply — the retrieve tool, the validator, the approval topic, the
trace emitter. You do not substitute anything by hand.

---

## 4 · Apply

```bash
terraform init
terraform plan
```

Read the plan. Specifically check:

- The write tool Lambda permissions name the **approval executor**, not the state machine
- Every Lambda has a `timeout`
- The KMS key policy is what you expect

```bash
terraform apply
```

---

## 5 · What the handlers must do

Terraform creates the functions. Their behavior is yours, and several architectural
properties depend entirely on it. Everything below is implemented in [src/](src/README.md)
— read this section to understand what those handlers are doing and why, before you change
them.

### Read tools

Return a **structured contract**, never free-form text. Bound the result set — a tool
returning ten thousand rows blows the context window and costs real money.

Errors should teach:

```json
{"error": "invalid_date_format", "expected": "YYYY-MM-DD", "received": "next tuesday"}
```

lets the model self-correct. `500 Internal Server Error` does not.

### Retrieval specifically

Apply **metadata filtering before semantic search** — by tenant, permission, date, type.
This is what prevents cross-tenant leakage, and the shared collection cannot do it for
you.

Treat every retrieved document as **untrusted**. A document in your corpus can contain
text phrased as instructions, and the model has no inherent way to tell it from yours. See
[AGENT-SECURITY.md](../../docs/agentic-coding-playbook/AGENT-SECURITY.md).

### The validator

Deterministic checks, in code, every time:

- **Ownership** — does the requesting user own the resource being acted on?
- **Permissions** — is this actor allowed to take this action at all?
- **Limits** — is the amount, count, or scope within policy?

Reject invalid proposals here rather than passing them to a human. That is what keeps
approval requests meaningful and prevents gate fatigue.

Write the proposal and its validation result to the approvals table before notifying.

### The executor

1. Verify the approval record matches the task token
2. Execute exactly the approved action — **with an idempotency key**, because agents retry
3. Record the outcome
4. Resolve the token with `SendTaskSuccess` or `SendTaskFailure`

Never execute something other than what was approved. The approval record is the contract.

### Trace emission

The metric filters in `modules/observability` match nothing unless handlers emit JSON logs
with the documented fields:

```json
{
  "event_type": "request_complete",
  "correlation_id": "abc-123",
  "model_version": "claude-opus-5",
  "prompt_version": "v7",
  "total_tokens": 4210,
  "cost_usd": 0.0631,
  "latency_ms": 3820,
  "outcome": "success"
}
```

`cost_usd` and `total_tokens` belong on the terminal record only — emitting them per step
multiply-counts them.

The orchestrator's own records — the terminal outcome of a request, the loop bound firing
— are produced by states inside the state machine, and a state machine writes to its
execution log group rather than to the trace group. They reach the filters through the
`trace_emitter` function, which the terminal states invoke. Omit it and the loop-bound and
cost alarms sit at zero forever, which reads exactly like a healthy system.

Two more things are easy to get wrong, and `shared/agentic_trace.py` handles both:

- The filters are attached to **one** log group, `/agentic/<prefix>/traces`, not to each
  function's own group. A handler that only prints to stdout looks healthy in the console
  and is invisible to every alarm. The module injects `TRACE_LOG_GROUP` and grants each
  role `logs:PutLogEvents` on it.
- Failing to emit a trace must not fail the request that produced it. An unobservable
  success beats a failure caused by observability.

---

## 6 · Verify the deployment

Evidence, not "should work":

```bash
# The split holds: write tools must NOT be invocable by the state machine.
aws lambda get-policy --function-name <project>-dev-tool-process_refund \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(json.loads(d['Policy'])['Statement'])"
```

Expect the principal to be the approval executor. If `states.amazonaws.com` appears there,
the gate is bypassed.

```bash
# Start an execution and watch it block on approval.
aws stepfunctions start-execution \
  --state-machine-arn "$(terraform output -raw state_machine_arn)" \
  --input '{"request": "test"}'
```

A write proposal should leave the execution in `RUNNING`, waiting on the token. If it
completes without a human acting, the gate is not wired.

---

## 7 · Prod

```bash
cd envs/prod
cp terraform.tfvars.example terraform.tfvars
```

Same modules, same wiring. What differs:

| | dev | prod |
|---|---|---|
| Knowledge collection | Public | VPC-only (`vpc_id` required) |
| Execution state PITR | Off | On |
| Execution data in logs | On | **Off** — payloads carry customer data |
| Log retention | 14 days | 365 days |
| Approval log retention | 30 days | 7 years |
| Archive expiry | 90 days | Your records policy |
| Alarm topics | Optional | **Required** |
| Loop bound | 12 steps | 8 steps |
| Approval timeout | 24h | 4h |

Work through [checklists/pre-apply.md](checklists/pre-apply.md) first.

---

## Troubleshooting

**`Error: Cycle: module.tools → module.approval → module.tools`**

You replaced a `local.*_arn` with a `module.*` reference. The deterministic ARNs in
`locals` exist to break that cycle — see the note at the top of `envs/dev/main.tf`.

**`InvalidParameterValueException: reserved concurrency exceeds account limit`**

Your account's unreserved concurrency floor is 100. Lower `reserved_concurrency` on the
tools, or request a limit increase.

**Guardrail resources fail with "unsupported"**

`create_guardrail` only applies when the model layer runs on Bedrock. Leave it `false`
when calling a vendor API directly.

**OpenSearch collection name too long**

Collection names cap at 32 characters. The `project` validation catches this at plan time —
shorten the project name.

**Approval never arrives**

Check the SNS subscription exists and is confirmed. An unconfirmed subscription silently
drops messages, and the execution sits until timeout. The `approvals-timing-out` alarm
catches this in aggregate.
