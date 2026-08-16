# The validator — BUILDING-BLOCKS.md section 6, step two of the enforcement flow.
#
#   The model proposes.  ← the reason tool, already happened
#   Application code decides.  ← here
#   A human authorizes.
#   The tool executes.
#
# Everything in this file is deterministic. "Only refund orders belonging to the requesting
# user" is a rule the model will follow almost always, and almost always is not an
# authorization model. The prompt is a hint; this code is the control.
#
# Rejecting here rather than forwarding also protects the human. An approver who is shown
# proposals that application code already knows are invalid learns to click approve, and a
# gate everyone clicks through is not a gate.
#
# ---------------------------------------------------------------------------
# Two entry paths, one function
# ---------------------------------------------------------------------------
#
# The Logic App calls this twice with different bodies:
#
#   validate — {correlation_id, tenant_id, proposal} → {valid, approval_id, reason}
#   notify   — {mode: "request_approval", approval_id, callback_url}
#
# The second publishes the approval request to Service Bus once a callback endpoint exists,
# so whatever surfaces approvals to humans has somewhere to send the resolution. It is here
# rather than in its own app because it writes the callback URL onto the same record this
# handler created, and splitting them would mean two principals writing one document.

import os
import time
import uuid

import cosmos_io
from agentic_trace import tracer_for
from contracts import fingerprint, positive_int

# Namespace for deterministic approval IDs. A retried validation produces the same
# approval_id, so the audit container shows one decision with revisions rather than two
# unrelated proposals.
_APPROVAL_NAMESPACE = uuid.UUID("6f9619ff-8b86-d011-b42d-00c04fc964ff")

# action -> role required to propose it. Absent from this map means not proposable at all; a
# new write tool is not approvable until someone adds it here deliberately.
REQUIRED_ROLES = {
    "process_refund": "refund_agent",
}


def run(payload):
    """The handler, minus the HTTP binding. Returns (body, status)."""
    if payload.get("mode") == "request_approval":
        return _notify(payload)

    tracer = tracer_for(payload, step="approval_validator")
    started = time.monotonic()

    proposal = payload.get("proposal") if isinstance(payload.get("proposal"), dict) else {}
    actor = payload.get("actor") if isinstance(payload.get("actor"), dict) else {}

    # Tenancy comes from the authenticated context the orchestrator carries, never from the
    # proposal — the proposal is the model's output and naming your own tenant is not an
    # authorization claim.
    if payload.get("tenant_id") and not actor.get("tenant_id"):
        actor = dict(actor, tenant_id=payload["tenant_id"])

    correlation_id = payload.get("correlation_id") or "unknown"

    checks = validate(proposal, actor)
    valid = all(check["passed"] for check in checks)
    reasons = [check["code"] for check in checks if not check["passed"]]

    approval_id = _approval_id(correlation_id, proposal)
    created_at = _now_iso()

    record = {
        "id": approval_id,
        "approval_id": approval_id,
        "created_at": created_at,
        "correlation_id": correlation_id,
        "status": "pending" if valid else "rejected",
        "action": proposal.get("action"),
        "arguments": proposal.get("arguments") or {},
        "arguments_fingerprint": fingerprint(proposal.get("arguments") or {}),
        "rationale": proposal.get("rationale"),
        "actor": {
            "user_id": actor.get("user_id"),
            "tenant_id": actor.get("tenant_id"),
            "roles": actor.get("roles") or [],
        },
        "validation": {"valid": valid, "checks": checks, "reasons": reasons},
    }

    # Written before anyone is notified. The record is the contract the executor will read
    # back; a notification that outruns the record is a notification about nothing.
    cosmos_io.put(record)

    tracer.emit(
        "approval_proposed",
        outcome="valid" if valid else "rejected",
        latency_ms=int((time.monotonic() - started) * 1000),
        approval_id=approval_id,
        action=proposal.get("action"),
        reasons=reasons or None,
    )
    tracer.flush()

    # `valid` is read directly by the Logic App's condition. approval_id travels on into the
    # Service Bus message and is the key the executor needs to find this record again.
    return {
        "valid": valid,
        "approval_id": approval_id,
        "created_at": created_at,
        "action": proposal.get("action"),
        "arguments_fingerprint": record["arguments_fingerprint"],
        "reason": reasons[0] if reasons else None,
        "reasons": reasons,
        "checks": checks,
    }, 200


def _notify(payload):
    """Publishes the approval request, and stamps the callback URL onto the record.

    Order matters. The URL is written first: a notification that reaches a human before the
    record can accept their answer produces an approval that resolves nothing, and the Logic
    App run sits until its window expires.
    """
    tracer = tracer_for(payload, step="approval_validator")

    approval_id = payload.get("approval_id")
    callback_url = payload.get("callback_url")
    if not approval_id or not callback_url:
        return {
            "ok": False,
            "error": "missing_required_fields",
            "expected": ["approval_id", "callback_url"],
        }, 400

    record = cosmos_io.get(approval_id)
    if not record:
        return {"ok": False, "error": "unknown_approval", "approval_id": approval_id}, 404

    record["callback_url"] = callback_url
    record["notified_at"] = _now_iso()
    cosmos_io.put(record)

    _publish(
        {
            "approval_id": approval_id,
            "correlation_id": payload.get("correlation_id"),
            "callback_url": callback_url,
            "action": record.get("action"),
            "arguments": record.get("arguments") or {},
            "rationale": record.get("rationale"),
            "actor": record.get("actor") or {},
        }
    )

    tracer.emit("approval_requested", outcome="published", approval_id=approval_id)
    tracer.flush()

    return {"ok": True, "approval_id": approval_id, "published": True}, 200


def _publish(message):
    """Sends the approval request to the Service Bus topic.

    Managed identity rather than a connection string: modules/approval sets
    `local_auth_enabled = false` on the namespace, so a SAS key would not work even if one
    were configured.
    """
    import json  # noqa: PLC0415

    from azure.identity import DefaultAzureCredential  # noqa: PLC0415
    from azure.servicebus import ServiceBusClient, ServiceBusMessage  # noqa: PLC0415

    namespace = os.environ.get("SERVICEBUS_NAMESPACE")
    topic = os.environ.get("APPROVAL_TOPIC")
    if not namespace or not topic:
        # Nothing surfaces the approval to a human. Loud rather than silent: the alternative
        # is a Logic App run that suspends and a queue nobody is watching.
        raise RuntimeError(
            "SERVICEBUS_NAMESPACE and APPROVAL_TOPIC must both be set on the validator."
        )

    credential = DefaultAzureCredential(
        managed_identity_client_id=os.environ.get("AZURE_CLIENT_ID")
    )
    with ServiceBusClient(
        fully_qualified_namespace=f"{namespace}.servicebus.windows.net",
        credential=credential,
    ) as client, client.get_topic_sender(topic_name=topic) as sender:
        sender.send_messages(ServiceBusMessage(json.dumps(message)))


def validate(proposal, actor):
    """Ownership, permissions, limits — in code, every time.

    Returns one entry per check so the audit record shows what was verified, not merely that
    something was.
    """
    action = proposal.get("action")
    arguments = (
        proposal.get("arguments") if isinstance(proposal.get("arguments"), dict) else {}
    )

    checks = [
        _check(
            "known_action",
            action in REQUIRED_ROLES,
            f"{action!r} is not an approvable action",
        ),
        _check(
            "actor_identified",
            bool(actor.get("user_id") and actor.get("tenant_id")),
            "actor.user_id and actor.tenant_id are required and come from the session",
        ),
    ]
    if not all(check["passed"] for check in checks):
        return checks

    checks.append(
        _check(
            "actor_permitted",
            REQUIRED_ROLES[action] in (actor.get("roles") or []),
            f"actor lacks role {REQUIRED_ROLES[action]!r}",
        )
    )
    checks.extend(_check_limits(action, arguments))
    checks.append(_check_ownership(action, arguments, actor))
    return checks


def _check_limits(action, arguments):
    if action != "process_refund":
        return []

    amount, invalid = positive_int(
        arguments.get("amount_cents"), "amount_cents", maximum=_policy_max_refund_cents()
    )
    return [
        _check(
            "within_limits",
            invalid is None,
            (invalid or {}).get("expected", "amount within policy"),
            detail={"amount_cents": amount} if amount is not None else None,
        )
    ]


def _check_ownership(action, arguments, actor):
    """INTEGRATION POINT — replace _resource_owner with your system of record.

    Fails closed. An ownership check that cannot reach its data source returns "not the
    owner", never "probably fine". That default is the difference between a degraded system
    and an open one.
    """
    resource_id = arguments.get("order_id")
    if not resource_id:
        return _check("actor_owns_resource", False, "no resource identified to check")

    try:
        owner = _resource_owner(action, str(resource_id))
    except Exception as exc:  # noqa: BLE001
        return _check("actor_owns_resource", False, f"ownership lookup unavailable: {exc}")

    return _check(
        "actor_owns_resource",
        owner is not None and owner == actor.get("user_id"),
        "requesting user does not own the resource",
        detail={"resource_id": str(resource_id)},
    )


def _resource_owner(action, resource_id):
    """Return the user_id that owns `resource_id`, or None if it cannot be determined.

    Point this at the orders service, the database, whatever holds the truth. Grant this
    app's identity read access to exactly that and nothing more — the validator decides, it
    does not act.
    """
    raise NotImplementedError(
        "approval_validator is a stub. Wire _resource_owner to your system of record; "
        f"it was asked who owns {resource_id!r} for action {action!r}."
    )


def _approval_id(correlation_id, proposal):
    seed = (
        f"{correlation_id}:{proposal.get('action')}:"
        f"{fingerprint(proposal.get('arguments') or {})}"
    )
    return str(uuid.uuid5(_APPROVAL_NAMESPACE, seed))


def _check(code, passed, detail_when_failed, detail=None):
    entry = {"code": code, "passed": bool(passed)}
    if not passed:
        entry["detail"] = detail_when_failed
    elif detail:
        entry["detail"] = detail
    return entry


def _policy_max_refund_cents():
    try:
        return int(os.environ.get("POLICY_MAX_REFUND_CENTS", 50_000))
    except ValueError:
        return 50_000


def _now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
