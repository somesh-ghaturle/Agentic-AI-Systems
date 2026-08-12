# The validator — BUILDING-BLOCKS.md section 6, step two of the enforcement flow.
#
#   The model proposes.  ← orchestrator, already happened
#   Application code decides.  ← here
#   A human authorizes.
#   The tool executes.
#
# Everything in this file is deterministic. "Only refund orders belonging to the
# requesting user" is a rule the model will follow almost always, and almost always is not
# an authorization model. The prompt is a hint; this code is the control.
#
# Rejecting here rather than forwarding also protects the human. An approver who is shown
# proposals that application code already knows are invalid learns to click approve, and
# a gate everyone clicks through is not a gate.

import os
import time
import uuid

import boto3

from agentic_trace import tracer_for
from contracts import fingerprint, positive_int
from ddb import to_item

# Namespace for deterministic approval IDs. A retried validation produces the same
# approval_id, so the audit table shows one decision with revisions rather than two
# unrelated proposals.
_APPROVAL_NAMESPACE = uuid.UUID("6f9619ff-8b86-d011-b42d-00c04fc964ff")

# action -> role required to propose it. Absent from this map means not proposable at all;
# a new write tool is not approvable until someone adds it here deliberately.
REQUIRED_ROLES = {
    "process_refund": "refund_agent",
}

_table = None


def handler(event, context=None):
    tracer = tracer_for(event, step="approval_validator")
    started = time.monotonic()

    decision = _unwrap(event.get("decision"))
    request = event.get("request") if isinstance(event.get("request"), dict) else {}
    actor = request.get("actor") if isinstance(request.get("actor"), dict) else {}
    correlation_id = event.get("correlation_id") or "unknown"

    checks = validate(decision, actor)
    valid = all(check["passed"] for check in checks)
    reasons = [check["code"] for check in checks if not check["passed"]]

    approval_id = _approval_id(correlation_id, decision)
    created_at = _now_iso()

    record = {
        "approval_id": approval_id,
        "created_at": created_at,
        "correlation_id": correlation_id,
        "status": "pending" if valid else "rejected",
        "action": decision.get("action"),
        "arguments": decision.get("arguments") or {},
        "arguments_fingerprint": fingerprint(decision.get("arguments") or {}),
        "rationale": decision.get("rationale"),
        "actor": {
            "user_id": actor.get("user_id"),
            "tenant_id": actor.get("tenant_id"),
            "roles": actor.get("roles") or [],
        },
        "validation": {"valid": valid, "checks": checks, "reasons": reasons},
    }

    # Written before anyone is notified. The record is the contract the executor will read
    # back; a notification that outruns the record is a notification about nothing.
    _write_record(record)

    tracer.emit(
        "approval_proposed",
        outcome="valid" if valid else "rejected",
        latency_ms=int((time.monotonic() - started) * 1000),
        approval_id=approval_id,
        action=decision.get("action"),
        reasons=reasons or None,
    )
    tracer.flush()

    # `valid` is read directly by the ValidationOutcome choice state. approval_id and
    # created_at travel on into the SNS message, and they are the composite key the
    # executor needs to find this record again.
    return {
        "valid": valid,
        "approval_id": approval_id,
        "created_at": created_at,
        "action": decision.get("action"),
        "arguments_fingerprint": record["arguments_fingerprint"],
        "reasons": reasons,
        "checks": checks,
    }


def validate(decision, actor):
    """Ownership, permissions, limits — in code, every time.

    Returns one entry per check so the audit record shows what was verified, not merely
    that something was.
    """
    action = decision.get("action")
    arguments = decision.get("arguments") if isinstance(decision.get("arguments"), dict) else {}

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
    owner", never "probably fine". That default is the difference between a degraded
    system and an open one.
    """
    resource_id = arguments.get("order_id")
    if not resource_id:
        return _check("actor_owns_resource", False, "no resource identified to check")

    try:
        owner = _resource_owner(action, str(resource_id))
    except Exception as exc:  # noqa: BLE001
        return _check(
            "actor_owns_resource", False, f"ownership lookup unavailable: {exc}"
        )

    return _check(
        "actor_owns_resource",
        owner is not None and owner == actor.get("user_id"),
        "requesting user does not own the resource",
        detail={"resource_id": str(resource_id)},
    )


def _resource_owner(action, resource_id):
    """Return the user_id that owns `resource_id`, or None if it cannot be determined.

    Point this at the orders service, the database, whatever holds the truth. Grant this
    role read access to exactly that and nothing more — the validator decides, it does not
    act.
    """
    raise NotImplementedError(
        "approval_validator is a stub. Wire _resource_owner to your system of record; "
        f"it was asked who owns {resource_id!r} for action {action!r}."
    )


def _write_record(record):
    global _table
    if _table is None:
        _table = boto3.resource("dynamodb").Table(os.environ["APPROVALS_TABLE"])
    # The arguments came from the model and can carry any JSON number. DynamoDB has no
    # float, so an unnormalized write raises and loses the proposal entirely.
    _table.put_item(Item=to_item(record))


def _approval_id(correlation_id, decision):
    seed = f"{correlation_id}:{decision.get('action')}:{fingerprint(decision.get('arguments') or {})}"
    return str(uuid.uuid5(_APPROVAL_NAMESPACE, seed))


def _unwrap(decision):
    """The orchestrator invokes tools through the Lambda integration, so a tool's return
    value arrives nested under Payload."""
    if isinstance(decision, dict):
        inner = decision.get("Payload")
        return inner if isinstance(inner, dict) else decision
    return {}


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
