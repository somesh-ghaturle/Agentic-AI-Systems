# Architecture — AWS

The claim this architecture makes is narrow and worth stating plainly:

> A state-changing action cannot reach production without a human approving that specific
> action, and that is enforced by IAM — not by the prompt, and not by the model choosing
> to behave.

Everything below exists to make that true, and to make it observable when it isn't.

---

## 1 · The whole system

Two paths leave the orchestrator. The read path is direct. The write path cannot be
walked without a human, and the boundary is drawn by IAM rather than by convention.

```mermaid
flowchart TB
    caller["Caller<br/><i>StartExecution</i>"]

    subgraph orch["Orchestrator — Step Functions"]
        sm["State machine<br/><i>execution budget 25h dev / 5h prod</i>"]
    end

    subgraph readpath["Read path — direct invocation"]
        retrieve["retrieve<br/><i>AI Search over the corpus</i>"]
        reason["reason<br/><i>the model step</i>"]
    end

    subgraph writepath["Write path — gated, no direct route"]
        validator["approval_validator<br/><i>ownership · permission · limits</i>"]
        topic["SNS approval topic<br/><i>KMS encrypted</i>"]
        human(["Human approver"])
        executor["approval_executor<br/><i>the ONLY write invoker</i>"]
        writetool["process_refund<br/><i>write tool</i>"]
    end

    subgraph data["State and evidence"]
        ddbstate[("Execution state<br/>DynamoDB")]
        ddbappr[("Approvals<br/>DynamoDB")]
        traces["Trace log group<br/><i>/agentic/PREFIX/traces</i>"]
        archive[("Archive<br/>S3 + Object Lock")]
    end

    caller --> sm
    sm --> retrieve
    sm --> reason
    sm --> validator
    validator --> ddbappr
    validator --> topic
    topic --> human
    human -->|"approve / reject"| executor
    executor --> ddbappr
    executor ==>|"only principal permitted"| writetool

    sm -.-> ddbstate
    retrieve -.-> traces
    reason -.-> traces
    executor -.-> traces
    traces --> archive

    sm -.->|"✗ no IAM path exists"| writetool

    classDef gate fill:#fff4e6,stroke:#d9822b,stroke-width:2px
    classDef denied stroke:#c0392b,stroke-width:2px,stroke-dasharray:4 3
    class validator,topic,human,executor gate
    class writetool denied
```

The dashed red edge is the point of the whole design: **there is no IAM path from the
state machine to a write tool.** Not a discouraged one — an absent one.

---

## 2 · Why the boundary holds — two independent locks

An architecture that depends on one check is one misconfiguration from being open. This
one requires both sides to agree, and neither side names the other's tools.

```mermaid
flowchart LR
    subgraph identity["Lock 1 — identity policy<br/>(what the caller may invoke)"]
        orole["Orchestrator role"]
        olist["read_tool_arns<br/>+ validator<br/>+ trace_emitter"]
        orole --> olist
    end

    subgraph resource["Lock 2 — resource policy<br/>(who may invoke this function)"]
        rt["read tools<br/><i>principal: states.amazonaws.com</i>"]
        wt["write tools<br/><i>principal: approval_executor ONLY</i>"]
    end

    olist -->|"allowed"| rt
    olist -.->|"✗ write ARNs never<br/>appear in the list"| wt

    exec["approval_executor role"] ==>|"allowed"| wt

    classDef ok fill:#eaf7ea,stroke:#2d8a34
    classDef no fill:#fdecea,stroke:#c0392b
    class rt ok
    class wt no
```

| Lock | Where | What it does |
|---|---|---|
| Identity policy | `modules/orchestration` | Grants `lambda:InvokeFunction` on an explicit ARN list — `read_tool_arns + validator + trace_emitter`. Write tool ARNs are never added, so there is nothing to accidentally over-grant. |
| Resource policy | `modules/tools` | `aws_lambda_permission.read_tool_from_orchestrator` names `states.amazonaws.com`; `write_tool_from_approval` names the executor. A write tool has no statement admitting the state machine. |

Remove either lock and the other still refuses. That redundancy is deliberate — no
blanket `lambda:InvokeFunction` on the account anywhere, which is the usual shortcut and
the one that turns a confused agent into lateral movement.

---

## 3 · Request lifecycle

The state machine as actually defined in `envs/*/state-machine.json.tftpl`.

```mermaid
flowchart TD
    init["InitializeTrace"] --> retrieve["Retrieve"]
    retrieve -->|"failure"| degraded["ReasonWithoutContext<br/><i>degraded, not fatal</i>"]
    retrieve --> reason["Reason"]
    degraded --> reason
    reason -->|"failure"| fail["RecordFailure"]
    reason --> incr["IncrementStep"]
    incr --> bound{"CheckLoopBound"}

    bound -->|"steps exceeded"| loopx["LoopBoundExceeded"]
    bound -->|"action_type = write"| validate["ValidateProposal"]
    bound -->|"action_type = continue"| retrieve
    bound -->|"default"| complete["Complete"]

    validate -->|"failure"| fail
    validate --> vout{"ValidationOutcome"}
    vout -->|"valid = false"| reject["RecordRejection<br/><i>no human troubled</i>"]
    vout -->|"valid"| await["AwaitHumanApproval<br/><b>waitForTaskToken</b><br/><i>24h dev / 4h prod</i>"]

    await -->|"approved"| success["RecordSuccess"]
    await -->|"States.Timeout"| abandoned["ApprovalAbandoned"]
    await -->|"States.ALL"| reject

    loopx --> recabandon["RecordAbandoned"]
    abandoned --> recabandon
    recabandon --> failx["FailExecution"]
    fail --> failx

    classDef gate fill:#fff4e6,stroke:#d9822b,stroke-width:2px
    classDef bad fill:#fdecea,stroke:#c0392b
    class await gate
    class failx,fail bad
```

Three routing decisions carry weight:

- **`CheckLoopBound` before anything else.** An agent that loops is an agent spending
  money. The bound is 12 steps in dev, 8 in prod, and exceeding it is a failure, not a
  quiet stop.
- **`ValidationOutcome` rejects before notifying.** Invalid proposals never reach a
  human. This is what keeps approval requests meaningful — a reviewer who sees mostly
  junk stops reading, and gate fatigue is how a gate fails while appearing to work.
- **`States.Timeout` is caught separately from `States.ALL`.** Nobody answering is not
  the same event as a human declining, and conflating them makes reviewer disengagement
  invisible. The catch order matters: `States.ALL` first would swallow the timeout.

---

## 4 · The approval round trip

`waitForTaskToken` is what makes the pause real. The execution is genuinely suspended —
not polling, not sleeping — and resumes only when someone resolves the token.

```mermaid
sequenceDiagram
    participant SM as State machine
    participant V as Validator
    participant D as Approvals table
    participant S as SNS + KMS
    participant H as Human
    participant E as Executor
    participant W as Write tool

    SM->>V: proposal + task token
    V->>V: ownership · permission · limits
    alt fails any check
        V-->>SM: valid = false
        Note over SM: rejected without<br/>troubling a human
    else passes
        V->>D: write record (pending) + fingerprint
        V->>S: publish approval request
        S->>H: notify
        Note over SM: execution SUSPENDED<br/>on the task token
        H->>E: approve
        E->>D: claim: pending → executing
        Note over E,D: conditional write —<br/>double-click collapses to one
        E->>E: re-check fingerprint
        E->>W: invoke with idempotency key
        W-->>E: result
        E->>D: record outcome
        E-->>SM: SendTaskSuccess
    end
```

Two failure modes this shape defends against:

**Replay and double-click.** The claim is a DynamoDB conditional write, so a redelivered
SNS message, a retried Lambda, and an impatient reviewer all collapse into one execution.

**Argument tampering between approval and execution.** The validator fingerprints the
arguments a human was shown; the executor re-computes it before invoking. A mismatch
fails the task rather than executing something nobody approved.

**A crashed executor.** If it dies between claiming and resolving the token, the record
sits in `executing` and the execution blocks until the window closes. A claim older than
`STALE_CLAIM_SECONDS` is therefore reclaimable — safe only because the write tool is
idempotent on the approval ID, which is what that key is for.

---

## 5 · Observability

Metric filters attach to **one** log group, `/agentic/PREFIX/traces` — not to each
function's own group. A handler that only prints to stdout looks healthy in the console
and is invisible to every alarm.

```mermaid
flowchart LR
    subgraph emitters["Emitters"]
        h["Handlers<br/><i>direct</i>"]
        smx["State machine<br/><i>via trace_emitter</i>"]
    end

    tg["/agentic/PREFIX/traces"]
    h --> tg
    smx --> tg

    tg --> f1["schema_validation_failed"]
    tg --> f2["loop_bound_exceeded"]
    tg --> f3["approval_abandoned"]
    tg --> f4["cost_usd on terminal record"]

    f1 --> a1(["Schema failures"])
    f2 --> a2(["Runaway loops"])
    f3 --> a3(["Gate fatigue"])
    f4 --> a4(["Daily spend"])

    aws["AWS/States<br/>ExecutionsTimedOut"] --> a5(["Budget overrun"])

    tg --> archive[("S3 archive<br/>Object Lock")]
```

A state machine writes to its *execution* log group, not the trace group, so the
orchestrator's own records — the terminal outcome, the loop bound firing — reach the
filters only through `trace_emitter`. Omit that function and the loop-bound and cost
alarms sit at zero forever, which reads exactly like a healthy system.

`cost_usd` and `total_tokens` belong on the **terminal** record only. Emitting them per
step multiply-counts spend.

---

## 6 · What Terraform builds

```mermaid
flowchart TB
    subgraph sec["security"]
        kms["KMS key<br/><i>lambda · sns · logs · s3 · dynamodb</i>"]
    end
    subgraph tools["tools"]
        lr["read tool Lambdas"]
        lw["write tool Lambdas"]
    end
    subgraph appr["approval"]
        val["validator"]
        exe["executor"]
        tbl[("approvals table")]
        sns["SNS topic"]
    end
    subgraph orc["orchestration"]
        sfn["state machine + role"]
    end
    subgraph obs["observability"]
        lg["trace log group"]
        mf["metric filters + alarms"]
        te["trace_emitter"]
    end
    subgraph st["state"]
        stt[("execution state")]
    end
    subgraph kb["knowledge"]
        aoss[("OpenSearch Serverless")]
    end
    subgraph arc["archive"]
        s3[("S3 + Object Lock")]
    end

    kms -.->|"encrypts"| appr
    kms -.->|"encrypts"| obs
    kms -.->|"encrypts"| arc
    sfn --> lr
    sfn --> val
    exe --> lw
    lr --> aoss
```

| Module | Creates | The load-bearing part |
|---|---|---|
| `security` | KMS key, optional Bedrock guardrail | Key policy must admit `sns.amazonaws.com`, or approval messages publish successfully and are never delivered |
| `tools` | One Lambda per tool, roles, resource policies | The `access` field drives the read/write split; roles need `kms:Decrypt` for encrypted env vars |
| `approval` | Approvals table, SNS topic, validator, executor | The executor is the only principal in write tools' resource policy |
| `orchestration` | State machine, role | ARN list excludes write tools by construction |
| `observability` | Trace log group, 4 metric filters, alarms, `trace_emitter` | Filters live on one shared group |
| `state` | Execution state table | PITR on in prod |
| `knowledge` | AI Search collection, access policies | Data access is separate from IAM — the principal must be the **retrieve tool's** role, not the orchestrator's |
| `archive` | S3 bucket, Object Lock | COMPLIANCE mode cannot be shortened by anyone, including root |

---

## 7 · Where the properties actually live

Infrastructure cannot enforce all of this. Some of it is only true if the code is right,
and it is worth being explicit about which is which.

| Property | Enforced by | If it breaks |
|---|---|---|
| Write tools unreachable without approval | **IAM** — identity + resource policy | Cannot break by editing a prompt |
| Approved arguments are what execute | **Code** — fingerprint re-check in the executor | Executes something nobody approved |
| Caller owns the resource | **Code** — `_resource_owner` in the validator | Approves a cross-tenant action |
| Retrieval is tenant-scoped | **Code** — filter inside the kNN clause, not beside it | Ranks other tenants' documents first, then hides them |
| Retries don't double-charge | **Code** — idempotency key in the write tool | A retry storm moves money twice |
| Failures are visible | **Config** — `TRACE_LOG_GROUP` + `trace_emitter` | Alarms sit at zero, indistinguishable from health |

The three `NotImplementedError` stubs sit squarely in the "Code" rows, and they raise
rather than returning a plausible default for exactly this reason. A reference
implementation that answers "yes, they own it" so the demo runs is how a stub reaches
production.
