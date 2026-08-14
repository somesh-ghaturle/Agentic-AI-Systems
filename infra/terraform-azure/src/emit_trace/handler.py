# Trace emitter — the Logic App's way into the trace pipeline.
#
# Why this app exists at all:
#
# Every alert in modules/observability reads `FunctionAppLogs`, filtered to this
# environment's apps by `_ResourceId has "<prefix>"`. That table is fed by the diagnostic
# settings on the FUNCTION APPS. A Logic App is not a function app: its own records go to
# `LogicAppWorkflowRuntime` and never appear in the table any of the queries read.
#
# So the orchestrator's own records — the terminal outcome of a request, the loop bound
# firing, an approval abandoned — would land outside every alert. That is the failure mode
# where the dashboard is green because nothing is reporting. This app is the orchestrator's
# way to write into a log the alerts actually read, and it is deliberately the only thing in
# the system that emits on the orchestrator's behalf.
#
# It is also deliberately forgiving: a trace that cannot be written must not fail the
# request it describes.

from agentic_trace import TERMINAL_EVENT, Tracer

# The vocabulary the observability module documents, plus "rejected", which the approval gate
# produces and which is neither a failure nor a success.
KNOWN_OUTCOMES = frozenset({"success", "failure", "abandoned", "escalated", "rejected"})


def run(payload):
    """The handler, minus the HTTP binding. Returns (body, status)."""
    record = normalize(payload)

    tracer = Tracer(record.pop("correlation_id"), step=record.pop("step", "orchestrator"))
    emitted = tracer.emit(record.pop("event_type"), **record)
    delivered = tracer.flush()

    return {"ok": True, "delivered": delivered, "record": emitted}, 200


def normalize(payload):
    """Shapes a Logic App payload into a trace record.

    Everything here is defensive on purpose. The alternative is reading fields out of the
    payload with direct expressions in the workflow definition, where one absent key is a
    runtime error that kills the run — which is how the loop-bound path fails before it can
    report that the loop bound was hit.
    """
    payload = payload if isinstance(payload, dict) else {}

    record = {
        # `event_type`, not `event`. The KQL in modules/observability matches
        # `trace.event_type`; the GCP tree uses the other name and they are not
        # interchangeable.
        "event_type": payload.get("event_type") or payload.get("event") or "step_complete",
        "correlation_id": payload.get("correlation_id") or payload.get("run_id") or "unknown",
        "step": payload.get("step") or "orchestrator",
    }

    outcome = payload.get("outcome")
    if outcome:
        record["outcome"] = outcome if outcome in KNOWN_OUTCOMES else f"other:{outcome}"

    for field in ("step_count", "max_steps", "latency_ms"):
        if payload.get(field) is not None:
            record[field] = payload[field]

    error = payload.get("error")
    if error is not None:
        record["error"] = _truncate(error)

    # Cost and tokens ride on the model step's own report of what it used. Absent that, they
    # are absent here — an invented number is worse than a gap, because a cost alert
    # calibrated against fiction is calibrated against nothing.
    if record["event_type"] == TERMINAL_EVENT:
        record.update(_usage(payload))

    return record


def _usage(payload):
    """Pulls usage out of the model step's return value, wherever it ended up.

    The Logic App calls tools with an HTTP action, so a handler's return value arrives under
    `body`. Both the wrapped and already-unwrapped shapes are accepted because the workflow
    may pass either.
    """
    decision = payload.get("decision")
    if isinstance(decision, dict):
        inner = decision.get("body")
        decision = inner if isinstance(inner, dict) else decision
    else:
        decision = {}

    # The reason handler flattens usage onto the response rather than nesting it under
    # `usage`. Both shapes are read so a nested caller still works.
    nested = decision.get("usage") if isinstance(decision.get("usage"), dict) else {}
    usage = {**decision, **nested}
    if not usage:
        usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}

    fields = {}
    for field in ("total_tokens", "input_tokens", "output_tokens", "cost_usd"):
        value = usage.get(field)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            fields[field] = value

    # Reproducibility: without these, a result cannot be tied to what produced it.
    for field in ("model_version", "prompt_version"):
        value = usage.get(field)
        if value:
            fields[field] = value

    return fields


def _truncate(value, limit=1000):
    text = value if isinstance(value, str) else repr(value)
    return text if len(text) <= limit else text[:limit] + "…"
