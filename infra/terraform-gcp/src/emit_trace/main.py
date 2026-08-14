# Trace emitter — the workflow's way into the trace log.
#
# Why this function exists at all:
#
# The log-based metrics in modules/observability are attached to ONE log,
# projects/<project>/logs/<prefix>-traces. The orchestrator's own records — the terminal
# outcome of a request, the loop bound firing — are produced by steps inside a Cloud
# Workflows execution, and a workflow writes to its own execution log, not to that one.
# Those two facts together mean the loop-bound alert and the cost alert watch a log nothing
# writes to, which is the failure mode where every dashboard is green because nothing is
# reporting.
#
# Cloud Workflows has a `sys.log` builtin, which looks like it removes the need for this
# function and does not: `sys.log` writes to the workflow's own execution log with the
# payload under a fixed field, so it lands outside `logName` every metric filters on. The
# entries are right there in the console, which is what makes it convincing.
#
# It is deliberately the only thing in the system that emits on the orchestrator's behalf,
# and it is deliberately forgiving: a trace that cannot be written must not fail the
# request it describes.

from agentic_trace import TERMINAL_EVENT, Tracer
from gcp_http import json_response, request_json

# The vocabulary the observability module documents, plus "rejected", which the approval
# gate produces and which is neither a failure nor a success.
KNOWN_OUTCOMES = frozenset({"success", "failure", "abandoned", "escalated", "rejected"})


def handler(request):
    record = normalize(request_json(request))

    tracer = Tracer(record.pop("correlation_id"), step=record.pop("step", "orchestrator"))
    emitted = tracer.emit(record.pop("event"), **record)
    delivered = tracer.flush()

    return json_response({"ok": True, "delivered": delivered, "record": emitted})


def normalize(payload):
    """Shapes a workflow payload into a trace record.

    Everything here is defensive on purpose. The alternative is reading fields out of the
    payload with direct expressions in the workflow YAML, where one absent key is a runtime
    error that kills the execution — which is how the loop-bound path fails before it can
    report that the loop bound was hit.
    """
    payload = payload if isinstance(payload, dict) else {}

    record = {
        # `event`, not `event_type`. modules/observability/main.tf filters on this exact
        # field name; the AWS tree uses the other one and they are not interchangeable.
        "event": payload.get("event") or payload.get("event_type") or "step_complete",
        "correlation_id": payload.get("correlation_id") or payload.get("execution_id") or "unknown",
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

    # Cost and tokens ride on the model step's own report of what it used. Absent that,
    # they are absent here — an invented number is worse than a gap, because a cost alert
    # calibrated against fiction is calibrated against nothing.
    if record["event"] == TERMINAL_EVENT:
        record.update(_usage(payload))

    return record


def _usage(payload):
    """Pulls usage out of the model step's return value, wherever it ended up.

    The workflow calls tools with http.post, so a handler's return value arrives under
    `body`. Both the wrapped and already-unwrapped shapes are accepted because the workflow
    may pass either.
    """
    decision = payload.get("decision")
    if isinstance(decision, dict):
        inner = decision.get("body")
        decision = inner if isinstance(inner, dict) else decision
    else:
        decision = {}

    # The GCP reason handler flattens usage onto the response rather than nesting it under
    # `usage` — Workflows has no comfortable way to reach into a nested object with a
    # default. Both shapes are read so a nested caller still works.
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
