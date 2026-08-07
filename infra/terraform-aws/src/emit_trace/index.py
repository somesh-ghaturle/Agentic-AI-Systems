# Trace emitter — the state machine's way into the trace log group.
#
# Why this function exists at all:
#
# The metric filters are attached to /agentic/<prefix>/traces. The orchestrator's own
# records — the terminal outcome of a request, the loop bound firing — are produced by
# states inside the state machine, and a state machine writes to its execution log group,
# not to that one. Those two facts together mean the loop-bound alarm and the cost alarm
# watch a log group nothing writes to, which is the failure mode where every dashboard is
# green because nothing is reporting.
#
# Step Functions can call CloudWatch Logs directly through the AWS SDK integration, which
# would avoid this Lambda entirely, except that PutLogEvents requires an epoch-millisecond
# timestamp and ASL has no intrinsic that converts a date to one. Hence a function.
#
# It is deliberately the only thing in the system that emits on the orchestrator's behalf,
# and it is deliberately forgiving: a trace that cannot be written must not fail the
# request it describes.

from agentic_trace import TERMINAL_EVENT, Tracer

# The vocabulary the observability module documents, plus "rejected", which the approval
# gate produces and which is neither a failure nor a success.
KNOWN_OUTCOMES = frozenset(
    {"success", "failure", "abandoned", "escalated", "rejected"}
)


def handler(event, context=None):
    record = normalize(event)

    tracer = Tracer(record.pop("correlation_id"), step=record.pop("step", "orchestrator"))
    emitted = tracer.emit(record.pop("event_type"), **record)
    delivered = tracer.flush()

    return {"ok": True, "delivered": delivered, "record": emitted}


def normalize(event):
    """Shapes a state machine payload into a trace record.

    Everything here is defensive on purpose. The alternative is reading fields out of the
    payload with `.$` paths in ASL, where one absent field is a runtime error that kills
    the execution — which is how the loop-bound path used to fail before it could report
    that the loop bound had been hit.
    """
    event = event if isinstance(event, dict) else {}

    record = {
        "event_type": event.get("event_type") or "step_complete",
        "correlation_id": event.get("correlation_id") or "unknown",
        "step": event.get("step") or "orchestrator",
    }

    outcome = event.get("outcome")
    if outcome:
        record["outcome"] = outcome if outcome in KNOWN_OUTCOMES else f"other:{outcome}"

    for field in ("step_count", "max_steps", "latency_ms"):
        if event.get(field) is not None:
            record[field] = event[field]

    error = event.get("error")
    if error is not None:
        record["error"] = _truncate(error)

    # Cost and tokens ride on the model step's own report of what it used. Absent that,
    # they are absent here — an invented number is worse than a gap, because a cost alarm
    # calibrated against fiction is calibrated against nothing.
    if record["event_type"] == TERMINAL_EVENT:
        record.update(_usage(event))

    return record


def _usage(event):
    """Pulls usage out of the model step's return value, wherever it ended up.

    The orchestrator invokes tools through the Lambda integration, so a handler's return
    value arrives nested under Payload. Both shapes are accepted because the state machine
    may pass either the wrapped result or an already-unwrapped one.
    """
    decision = event.get("decision")
    if isinstance(decision, dict):
        inner = decision.get("Payload")
        decision = inner if isinstance(inner, dict) else decision
    else:
        decision = {}

    usage = decision.get("usage") if isinstance(decision.get("usage"), dict) else {}
    usage = usage or (event.get("usage") if isinstance(event.get("usage"), dict) else {})

    fields = {}
    for source, target in (
        ("total_tokens", "total_tokens"),
        ("input_tokens", "input_tokens"),
        ("output_tokens", "output_tokens"),
        ("cost_usd", "cost_usd"),
    ):
        value = usage.get(source)
        if isinstance(value, (int, float)):
            fields[target] = value

    # Reproducibility: without these, a result cannot be tied to what produced it.
    for field in ("model_version", "prompt_version"):
        value = decision.get(field) or usage.get(field)
        if value:
            fields[field] = value

    return fields


def _truncate(value, limit=1000):
    text = value if isinstance(value, str) else repr(value)
    return text if len(text) <= limit else text[:limit] + "…"
