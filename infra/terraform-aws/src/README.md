# Handler source

Terraform creates the functions. These are the handlers that go in them, and several of
the architecture's properties live here rather than in the `.tf` files — the infrastructure
can enforce *who may invoke a write tool*, but only code can enforce *that the caller owns
the thing they are writing to*.

```
shared/            copied into every package at build time
  agentic_trace.py trace records that the observability metric filters actually match
  contracts.py     structured results and errors the model can act on
  aoss.py          SigV4-signed OpenSearch Serverless client, no third-party deps
retrieve/          read tool  — invoked directly by the orchestrator
process_refund/    write tool — invocable ONLY by the approval executor
approval_validator/ deterministic ownership, permission, and limit checks
approval_executor/ the only principal that invokes write tools
```

## Build

```bash
./build.sh          # writes ../build/*.zip, which terraform.tfvars points at
```

Run it before `terraform plan`. The modules read the zips with `filebase64sha256` at plan
time, so a missing package fails immediately rather than halfway through an apply.

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
| `MAX_REFUND_CENTS` | process_refund | The tool's own ceiling, independent of the validator's. |
| `POLICY_MAX_REFUND_CENTS` | approval_validator | The policy limit checked before a human is asked. |
| `WRITE_TOOL_PREFIX` | approval_executor | Wired by the env root modules. |

## The contract between these handlers and the state machine

`envs/*/state-machine.json` reads three fields by path, so their names are load-bearing:

- `$.decision.Payload.action_type` — `"write"` routes to the approval gate
- `$.validation.Payload.valid` — `false` routes to rejection without troubling a human
- `$.validation.Payload.approval_id` / `.created_at` — the composite key the SNS message
  carries to the approver, and the only way the executor finds the record again

Rename any of those and the gate stops gating, quietly.
