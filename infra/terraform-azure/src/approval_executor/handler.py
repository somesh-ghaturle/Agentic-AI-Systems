# The executor — BUILDING-BLOCKS.md section 6, step four of the enforcement flow.
#
# This is the only principal in the system permitted to invoke a write tool. It is the
# component that makes "the model cannot directly cause an irreversible action" a property
# of the system rather than a hope about the prompt.
#
# ---------------------------------------------------------------------------
# The Azure caveat, stated plainly
# ---------------------------------------------------------------------------
#
# On AWS the orchestrator physically lacks lambda:InvokeFunction on the write tools. On GCP
# a deny policy overrides any allow. Here the boundary is ONE lock: the write tool's Entra
# application sets `app_role_assignment_required = true`, and only this app's identity holds
# the role.
#
# That lock is weaker than the other two in a specific way — an app role assignment added in
# the portal opens the write path with no code change and no Terraform diff. Nothing in this
# file can compensate for that; it is why modules/entra-audit exists as a detective control
# and why tests/test_write_boundary.py asserts the flag is never flipped to false.
#
# Invoked by whatever surfaces the approval to a human — a Teams action, an internal console,
# an email callback. That caller supplies the identity of the approval and the callback URL
# it was handed, and nothing else that matters:
#
#   {"approval_id": "...", "callback_url": "...",
#    "decision": "approve" | "reject", "approver": {"user_id": "..."}, "comment": "..."}
#
# The action and its arguments are read back from the approval record, never from this
# request. The record is what a human saw and agreed to; the request is an untrusted claim
# about it. Executing anything other than the record would make the approval decorative, and
# "approve a $50 refund, execute a $5,000 one" is one edited field away.

import json
import os
import time

import cosmos_io
from agentic_trace import tracer_for
from azure_http import post_with_identity, resolve_callback
from contracts import fingerprint, require


def run(payload):
    """The handler, minus the HTTP binding. Returns (body, status)."""
    tracer = tracer_for(payload, step="approval_executor")
    started = time.monotonic()

    fields, missing = require(payload, "approval_id", "callback_url", "decision")
    if missing:
        tracer.emit("approval_callback_malformed", outcome="failure", **missing)
        tracer.flush()
        return missing, 400

    decision = str(fields["decision"]).lower()
    if decision not in ("approve", "reject"):
        tracer.flush()
        return {
            "ok": False,
            "error": "invalid_decision",
            "expected": ["approve", "reject"],
            "received": decision,
        }, 400

    approval_id = fields["approval_id"]
    callback_url = fields["callback_url"]
    approver = payload.get("approver") or {}

    if decision == "reject":
        result = _reject(approval_id, callback_url, approver, payload.get("comment"), tracer)
    else:
        result = _approve(approval_id, callback_url, approver, tracer)

    tracer.emit(
        "approval_resolved",
        outcome=result.get("status", "unknown"),
        latency_ms=int((time.monotonic() - started) * 1000),
        approval_id=approval_id,
        decision=decision,
    )
    tracer.flush()
    return result, 200


def _approve(approval_id, callback_url, approver, tracer):
    # The claim is the concurrency control and the replay guard in one operation. Only a
    # record still `pending` (or one whose claim has gone stale) can be claimed, so a
    # double-clicked approve button, a redelivered Service Bus message, and a retried
    # invocation all collapse into one execution. See shared/cosmos_io.py for why this needs
    # an ETag on Azure where DynamoDB needed a condition expression.
    record, previous_status = cosmos_io.claim(
        approval_id, "executing", callback_url, approver
    )
    if record is None:
        return _already_resolved(approval_id, tracer)

    if previous_status == "executing":
        # A previous executor claimed this and died before resolving the callback. Worth its
        # own event: without one, the recovery is invisible and the incident reads as a slow
        # approver rather than a crashed executor.
        tracer.emit(
            "approval_claim_reclaimed",
            outcome="reclaimed",
            approval_id=approval_id,
            previous_claimed_at=record.get("claimed_at"),
        )

    action = record.get("action")
    arguments = record.get("arguments") or {}

    # Belt and braces: the fingerprint the validator computed over the arguments a human was
    # shown must still describe the arguments about to run.
    stored = record.get("arguments_fingerprint")
    if stored and stored != fingerprint(arguments):
        cosmos_io.record_outcome(approval_id, "failed", {"error": "arguments_tampered"})
        _resolve(
            callback_url,
            {
                "status": "failed",
                "error": "ApprovalTampered",
                "cause": "Arguments no longer match the approved proposal.",
            },
        )
        return {"status": "failed", "error": "arguments_tampered"}

    body, failed = _invoke_write_tool(
        action,
        {
            "approval_id": approval_id,
            "correlation_id": record.get("correlation_id"),
            # The approval ID is the idempotency key. It is stable across every retry of this
            # execution and unique to this approved action, which is exactly the property a
            # payment provider's idempotency header needs.
            "idempotency_key": approval_id,
            "arguments": arguments,
        },
    )

    if failed:
        cosmos_io.record_outcome(approval_id, "failed", body)
        _resolve(callback_url, {"status": "failed", "error": "WriteToolFailed", "cause": body})
        return {"status": "failed", "approval_id": approval_id, "result": body}

    cosmos_io.record_outcome(approval_id, "executed", body)
    _resolve(
        callback_url, {"status": "executed", "approval_id": approval_id, "result": body}
    )
    return {"status": "executed", "approval_id": approval_id, "result": body}


def _reject(approval_id, callback_url, approver, comment, tracer):
    record, _ = cosmos_io.claim(approval_id, "rejected", callback_url, approver, comment=comment)
    if record is None:
        return _already_resolved(approval_id, tracer)

    # A rejection is a designed failure path, not an error. The Logic App reads the status
    # and records the rejection rather than failing the run.
    _resolve(
        callback_url,
        {
            "status": "rejected",
            "error": "ApprovalRejected",
            "cause": comment or "Rejected by approver.",
        },
    )
    return {"status": "rejected", "approval_id": approval_id}


def _invoke_write_tool(action, payload):
    """Invokes the write tool over HTTP with this app's own identity.

    Returns (body, failed). The URL and scope come from a map supplied by modules/approval
    rather than from string interpolation on the action name, so an action nobody registered
    fails here — visibly, before any call is made — rather than resolving to a plausible URL.
    """
    target = _write_tool_target(action)
    try:
        status, body = post_with_identity(
            target["url"],
            payload,
            scope=target["scope"],
            timeout=_write_tool_timeout(),
        )
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}, True

    if status in (401, 403):
        # The one failure worth naming. Easy Auth returns 401 when this identity has no app
        # role on the target, and the same 401 when the token was requested for the wrong
        # scope. Both look identical to "wrong URL" without this hint.
        return {
            "error": "write_tool_forbidden",
            "detail": (
                f"{status} from the write tool: check the app role assignment for this "
                "identity on the tool's Entra application, and that the token scope is "
                f"{target['scope']!r}."
            ),
            "body": body,
        }, True

    failed = status >= 400 or not (isinstance(body, dict) and body.get("ok", False))
    return body, failed


def _resolve(callback_url, outcome):
    """Resumes the suspended Logic App run.

    A failure here is not recoverable by retrying the write — the write already happened. It
    propagates so the invocation is visibly failed rather than reporting success for a run
    still hanging at its callback.
    """
    resolve_callback(callback_url, outcome)


def _write_tool_target(action):
    """Write tools are addressed by a map, not by name interpolation.

    Two settings, both written by the env root from modules/tools outputs and both filtered
    to write tools only:

      WRITE_TOOL_URLS       {action: https://<app>.azurewebsites.net/api/<action>}
      WRITE_TOOL_AUDIENCES  {action: api://<prefix>-tool-<action>}

    They are separate rather than one nested map because they come from two different
    resources — the function app and its Entra application — and joining them in Terraform
    would obscure which one is missing when a tool is half-registered. Joining them here
    means this function can say exactly that.

    An action absent from either map raises, so registering a new write tool is a deliberate
    act in Terraform rather than a naming convention the model can satisfy on its own.
    """
    urls = _json_setting("WRITE_TOOL_URLS")
    audiences = _json_setting("WRITE_TOOL_AUDIENCES")

    url = urls.get(action)
    audience = audiences.get(action)

    if not url and not audience:
        raise RuntimeError(
            f"{action!r} is not a registered write tool. Known: {sorted(urls)}"
        )
    # Half-registered is worth distinguishing from unregistered: it means the tool exists
    # but something in modules/tools did not produce both halves, and the resulting 401
    # would otherwise be blamed on the app role assignment.
    if not url:
        raise RuntimeError(f"{action!r} has an audience but no URL in WRITE_TOOL_URLS.")
    if not audience:
        raise RuntimeError(f"{action!r} has a URL but no audience in WRITE_TOOL_AUDIENCES.")

    # The audience is the resource; the scope adds /.default, which is what asks for the
    # app roles already assigned to this identity rather than a delegated permission.
    return {"url": url, "scope": f"{audience}/.default"}


def _json_setting(name):
    raw = os.environ.get(name)
    if not raw:
        raise RuntimeError(f"{name} is not set on the executor app.")
    try:
        value = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"{name} is not valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{name} must be a JSON object of action -> value.")
    return value


def _already_resolved(approval_id, tracer):
    """A replay, or a second approver arriving late.

    The callback belonging to this approval was already resolved, so resolving it again would
    fail. Report and stop — this is the correct outcome, not an error to retry.
    """
    current = cosmos_io.get(approval_id)
    tracer.emit(
        "approval_replay_ignored",
        outcome="ignored",
        approval_id=approval_id,
        current_status=current.get("status", "missing"),
    )
    return {
        "status": "already_resolved",
        "approval_id": approval_id,
        "current_status": current.get("status", "missing"),
    }


def _write_tool_timeout():
    try:
        return int(os.environ.get("WRITE_TOOL_TIMEOUT_SECONDS", 60))
    except ValueError:
        return 60
