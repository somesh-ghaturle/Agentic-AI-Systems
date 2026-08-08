# Handler source

Terraform creates the functions. These are the handlers that go in them, and several of
the architecture's properties live here rather than in the `.tf` files — the infrastructure
can enforce *who may invoke a write tool*, but only code can enforce *that the caller owns
the thing they are writing to*.

```
shared/            copied into every package at build time
  agentic_trace.py trace records that the observability metric filters actually match
  contracts.py     structured results and errors the model can act on
  ddb.py           float/Decimal marshalling — DynamoDB has no float, boto3 raises
  aoss.py          SigV4-signed OpenSearch Serverless client, no third-party deps
retrieve/          read tool  — invoked directly by the orchestrator
reason/            read tool  — the model step; proposes, never executes
process_refund/    write tool — invocable ONLY by the approval executor
approval_validator/ deterministic ownership, permission, and limit checks
approval_executor/ the only principal that invokes write tools
emit_trace/        the orchestrator's way into the trace log group
```

`reason` is classified `read` because it only ever proposes: its `action_type: "write"`
routes a proposal into validation and human approval, and it has no path to a write tool
of its own. It is also the one package with a dependency — the Anthropic SDK, declared in
its own `requirements.txt` and installed only into its zip. Everything else runs on what
the Lambda runtime already ships.

`emit_trace` is not a tool. The model never proposes it and it takes no arguments from the
model — it exists because the metric filters live on one log group and a state machine
writes to a different one, so the records produced inside the orchestrator (the terminal
outcome of a request, the loop bound firing) never reach the filters on their own. Step
Functions could call `PutLogEvents` directly through the AWS SDK integration and skip the
Lambda, except the API wants an epoch-millisecond timestamp and ASL has no intrinsic that
produces one.

## Build

```bash
./build.sh          # writes ../build/*.zip, which terraform.tfvars points at
```

Run it before `terraform plan`. The modules read the zips with `filebase64sha256` at plan
time, so a missing package fails immediately rather than halfway through an apply.

Packages with a `requirements.txt` get their dependencies installed into the zip, with
wheels resolved for the **Lambda** platform rather than the build machine's — building on
a Mac and shipping native wheels to Amazon Linux is the classic way to get an
`ImportError` that only appears after deploy. Override `LAMBDA_PLATFORM`,
`LAMBDA_PYTHON`, or `PYTHON` if your runtime differs.

## Test

```bash
python3 -m unittest discover -s tests -v
```

No AWS, no credentials, no dependencies — the tests stub `boto3` and exercise the parts
that are pure logic: the filter construction, the error contracts, the validator's checks,
and the rule that cost only appears on terminal trace records.

## The three stubs, and why they raise

Three functions raise `NotImplementedError` on purpose. Each is a place where a plausible
default would be actively dangerous:

| Function | File | Replace with |
|---|---|---|
| `_resource_owner` | `approval_validator/validator.py` | your system of record for ownership |
| `_submit_refund` | `process_refund/index.py` | your payment provider, passing the idempotency key |
| `_embed` | `retrieve/index.py` | set `EMBEDDING_MODEL_ID` — it works once you do |

The model step is not among them: `reason/` is a working handler. What it needs from you
is the cost rates (`INPUT_COST_PER_MTOK` / `OUTPUT_COST_PER_MTOK`), because Bedrock is
partner-operated and prices separately from the first-party API. Leave them unset and
traces carry token counts with no cost — which leaves the daily-cost alarm nothing to
count, but is more honest than a figure derived from the wrong price list.

A reference implementation that returns "yes, they own it" so the demo runs is how a stub
reaches production. Ownership checks fail closed; the refund stub refuses rather than
pretending to move money.

## Environment

Terraform injects `APPROVALS_TABLE`, `TOOL_NAME`, and `TOOL_ACCESS`. The rest come from
`common_environment` and the per-function `environment` maps in `terraform.tfvars`:

| Variable | Used by | Notes |
|---|---|---|
| `TRACE_LOG_GROUP` | all | Wired by the env root modules. Without it traces go to stdout only, and every alarm stays silent. |
| `KNOWLEDGE_COLLECTION` | retrieve | Collection name; the endpoint is resolved from it at cold start. |
| `KNOWLEDGE_INDEX` | retrieve | Defaults to `knowledge`. |
| `EMBEDDING_MODEL_ID` | retrieve | Needs `bedrock:InvokeModel` in the tool's `policy_json`. |
| `MAX_DOCUMENT_CHARS` | retrieve | Per-document truncation, default 2000. |
| `MODEL_ID` | reason | Bedrock model id — note the `anthropic.` prefix. Defaults to `anthropic.claude-opus-5`. |
| `MODEL_EFFORT` | reason | `low`–`max`, default `high`. `xhigh` is the recommended setting for agentic work. |
| `MAX_TOKENS` | reason | Caps thinking **and** response together, default 16000. |
| `INPUT_COST_PER_MTOK` | reason | From the **Bedrock** price list, not Anthropic's. Unset means no `cost_usd` on traces. |
| `OUTPUT_COST_PER_MTOK` | reason | Same. |
| `MAX_REFUND_CENTS` | process_refund | The tool's own ceiling, independent of the validator's. |
| `POLICY_MAX_REFUND_CENTS` | approval_validator | The policy limit checked before a human is asked. |
| `WRITE_TOOL_PREFIX` | approval_executor | Wired by the env root modules. |
| `STALE_CLAIM_SECONDS` | approval_executor | How long an `executing` claim may sit before another executor may take it over, default 900. Must exceed the write tool's timeout plus retries. |

## The contract between these handlers and the state machine

`envs/*/state-machine.json.tftpl` reads three fields by path, so their names are
load-bearing:

- `$.decision.Payload.action_type` — `"write"` routes to the approval gate
- `$.validation.Payload.valid` — `false` routes to rejection without troubling a human
- `$.validation.Payload.approval_id` / `.created_at` — the composite key the SNS message
  carries to the approver, and the only way the executor finds the record again

Rename any of those and the gate stops gating, quietly.
