# The executor — BUILDING-BLOCKS.md section 6, step four of the enforcement flow.
#
# This is the only principal in the system permitted to invoke a write tool. It is the
# component that makes "the model cannot directly cause an irreversible action" a property
# of the system rather than a hope about the prompt.
#
# On GCP that exclusivity is drawn twice, which is worth knowing before changing either:
#
#   1. Only this function's service account holds `roles/run.invoker` on the write tools'
#      Cloud Run services. That is the positive grant, in modules/tools.
#   2. `google_iam_deny_policy.write_boundary` in modules/orchestration denies the
#      orchestrator's service account the ability to invoke them at all, and a deny beats
#      any allow — including one added later by someone who does not know about this file.
#
# There is a specific trap the first control has to avoid: for gen2 Cloud Functions,
# `roles/cloudfunctions.invoker` does NOT gate invocation. Gen2 functions are Cloud Run
# services underneath and the check that actually runs is `run.invoker` on the underlying
# service. Granting the cloudfunctions role instead produces a boundary that looks correct
# in the console and admits everyone.
#
# Invoked by whatever surfaces the approval to a human — a Slack action, an internal
# console, an email callback. That caller supplies the identity of the approval and the
# callback URL it was handed, and nothing else that matters:
#
#   {"approval_id": "...", "callback_url": "...",
#    "decision": "approve" | "reject", "approver": {"user_id": "..."}, "comment": "..."}
#
# The action and its arguments are read back from the approval record, never from this
# request. The record is what a human saw and agreed to; the request is an untrusted claim
# about it. Executing anything other than the record would make the approval decorative,
# and "approve a $50 refund, execute a $5,000 one" is one edited field away.

import os
import time

import firestore_io
from agentic_trace import tracer_for
from contracts import fingerprint, require
from gcp_http import json_response, post_with_identity, request_json, resolve_callback


def handler(request):
    payload = request_json(request)
    tracer = tracer_for(payload, step="approval_executor")
    started = time.monotonic()

    fields, missing = require(payload, "approval_id", "callback_url", "decision")
    if missing:
        tracer.emit("approval_callback_malformed", outcome="failure", **missing)
        tracer.flush()
        return json_response(missing, status=400)

    decision = str(fields["decision"]).lower()
    if decision not in ("approve", "reject"):
        tracer.flush()
        return json_response(
            {
                "ok": False,
                "error": "invalid_decision",
                "expected": ["approve", "reject"],
                "received": decision,
            },
            status=400,
        )

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
    return json_response(result)


def _approve(approval_id, callback_url, approver, tracer):
    # The claim is the concurrency control and the replay guard in one transaction. Only a
    # record still `pending` (or one whose claim has gone stale) can be claimed, so a
    # double-clicked approve button, a redelivered Pub/Sub message, and a retried function
    # invocation all collapse into one execution. See shared/firestore_io.py for why this
    # needs a transaction on GCP where DynamoDB needed only a condition expression.
    record, previous_status = firestore_io.claim(
        approval_id, "executing", callback_url, approver
    )
    if record is None:
        return _already_resolved(approval_id, tracer)

    if previous_status == "executing":
        # A previous executor claimed this and died before resolving the callback. Worth
        # its own event: without one, the recovery is invisible and the incident reads as a
        # slow approver rather than a crashed executor.
        tracer.emit(
            "approval_claim_reclaimed",
            outcome="reclaimed",
            approval_id=approval_id,
            previous_claimed_at=record.get("claimed_at"),
        )

    action = record.get("action")
    arguments = record.get("arguments") or {}

    # Belt and braces: the fingerprint the validator computed over the arguments a human
    # was shown must still describe the arguments about to run.
    stored = record.get("arguments_fingerprint")
    if stored and stored != fingerprint(arguments):
        firestore_io.record_outcome(approval_id, "failed", {"error": "arguments_tampered"})
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
            "correlation_id": record.get("execution_id"),
            # The approval ID is the idempotency key. It is stable across every retry of
            # this execution and unique to this approved action, which is exactly the
            # property a payment provider's idempotency header needs.
            "idempotency_key": approval_id,
            "arguments": arguments,
        },
    )

    if failed:
        firestore_io.record_outcome(approval_id, "failed", body)
        _resolve(
            callback_url,
            {"status": "failed", "error": "WriteToolFailed", "cause": body},
        )
        return {"status": "failed", "approval_id": approval_id, "result": body}

    firestore_io.record_outcome(approval_id, "executed", body)
    _resolve(callback_url, {"status": "executed", "approval_id": approval_id, "result": body})
    return {"status": "executed", "approval_id": approval_id, "result": body}


def _reject(approval_id, callback_url, approver, comment, tracer):
    record, _ = firestore_io.claim(
        approval_id, "rejected", callback_url, approver, comment=comment
    )
    if record is None:
        return _already_resolved(approval_id, tracer)

    # A rejection is a designed failure path, not an error. The workflow reads the status
    # and records the rejection rather than failing the execution.
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
    """Invokes the write tool over HTTP with this function's own identity.

    Returns (body, failed). The URL comes from a map supplied by modules/approval rather
    than from string interpolation on the action name, so an action nobody registered fails
    here — visibly, before any call is made — rather than resolving to a plausible URL.
    """
    url = _write_tool_url(action)
    try:
        status, body = post_with_identity(url, payload, timeout=_write_tool_timeout())
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}, True

    if status == 403:
        # The one failure worth naming. A 403 here means this service account has lost
        # run.invoker on the target, or the token was minted for the wrong audience — see
        # shared/gcp_http.py. Both look identical to "wrong URL" without this hint.
        return {
            "error": "write_tool_forbidden",
            "detail": "403 from the write tool: check roles/run.invoker on its Cloud Run "
            "service, and that the OIDC audience is the target URL.",
            "body": body,
        }, True

    failed = status >= 400 or not (isinstance(body, dict) and body.get("ok", False))
    return body, failed


def _resolve(callback_url, outcome):
    """Resumes the suspended workflow execution.

    A failure here is not recoverable by retrying the write — the write already happened.
    It is recorded and re-raised so the invocation is visibly failed rather than reporting
    success for an execution still hanging at its callback.
    """
    resolve_callback(callback_url, outcome)


def _write_tool_url(action):
    """Write tools are addressed by a URL map, not by name interpolation.

    WRITE_TOOL_URLS is a JSON object of {action: url} written by modules/approval from the
    actual Cloud Run service URIs. An unlisted action raises rather than guessing.
    """
    import json  # noqa: PLC0415

    raw = os.environ.get("WRITE_TOOL_URLS")
    if not raw:
        raise RuntimeError("WRITE_TOOL_URLS is not set on the executor function.")

    try:
        urls = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"WRITE_TOOL_URLS is not valid JSON: {exc}") from exc

    url = urls.get(action)
    if not url:
        raise RuntimeError(
            f"{action!r} is not a registered write tool. Known: {sorted(urls)}"
        )
    return url


def _already_resolved(approval_id, tracer):
    """A replay, or a second approver arriving late.

    The callback belonging to this approval was already resolved, so resolving it again
    would fail. Report and stop — this is the correct outcome, not an error to retry.
    """
    current = firestore_io.get(approval_id)
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
