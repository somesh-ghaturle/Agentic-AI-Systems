# Hermes — architecture

The router and the write boundary in one picture. [README.md](README.md) explains the
reasoning; this page is the diagram and just enough text to read it.

```mermaid
flowchart TB
    REQ["Request"] --> ROUTE["Hermes router<br/>ordered rules, first match wins"]

    subgraph NOAUTH["Router process — holds the read registry only"]
        ROUTE --> HANDLER["Handler<br/>research · status · act"]
        HANDLER --> BELT["Toolbelt<br/>refuses anything not read"]
        BELT --> READTOOLS["Read tools<br/>kb_search · fetch_document · service_status"]
    end

    READTOOLS --> ANSWER["Answer returned"]
    HANDLER -- "wants to change state" --> PROPOSAL["WriteProposal<br/>tool + arguments + fingerprint"]

    PROPOSAL --> GATE{"Human approves<br/>this exact action?"}
    GATE -- "no" --> PENDING["Request ends pending<br/>nothing has changed"]
    GATE -- "yes" --> APPROVAL["Approval<br/>bound to fingerprint · single-use · expiring"]

    subgraph AUTH["Approval executor — sole holder of the write registry"]
        APPROVAL --> CLAIM["Claim: compare-and-set"]
        CLAIM --> WRITETOOLS["Write tools<br/>restart_service · post_message · delete_record"]
    end

    WRITETOOLS --> EFFECT["State changed, trace recorded"]

    ROUTE -.-> TRACE["Trace<br/>one event per hop, one trace_id"]
    BELT -.-> TRACE
    PROPOSAL -.-> TRACE
    CLAIM -.-> TRACE

    classDef boundary fill:#f8f9fa,stroke:#333,stroke-width:1px
    class NOAUTH,AUTH boundary
```

## Reading it

**The two boxes are two objects, not two phases.** `Hermes` is constructed with the read
registry and refuses the write one; `ApprovalExecutor` is constructed with the write
registry and refuses the read one. They share an approval store and nothing else. No arrow
crosses from the upper box into the lower one, and that absence is the design: the router
holds no reference that reaches a write tool.

**The only path between them runs through a human.** A handler that wants to change state
returns a `WriteProposal` — inert data carrying the tool name, the exact arguments, and a
fingerprint of both. The run ends there. Approving resumes it; not approving leaves a
request that completed normally, having changed nothing.

**The claim is a compare-and-set, and it happens before the tool runs.** Reversing those
two would leave a crash between them with the action done and the token still spendable.

**The dotted edges are the trace.** Every hop emits one event under a shared `trace_id`, so
a run reads back as an ordered account of what happened and why. That stream is what
[examples/trace-eval](../trace-eval/README.md) scores — it is the only place the fact "this
write was authorised" is recorded, since it never reaches the answer the user sees.

## Related

- [README.md](README.md) — the reasoning, the tests, and what this example is not
- [examples/trace-eval/](../trace-eval/README.md) — scoring the path this diagram describes
- [infra/](../../infra/) — the same boundary drawn with cloud IAM instead of Python
