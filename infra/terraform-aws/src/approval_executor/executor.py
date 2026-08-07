# The executor — BUILDING-BLOCKS.md §6, step four of the enforcement flow.
#
# This is the only principal in the system permitted to invoke a write tool. It is the
# component that makes "the model cannot directly cause an irreversible action" a property
# of the system rather than a hope about the prompt.
#
# Invoked by whatever surfaces the approval to a human — a Slack action, an internal
# console, an email callback. That caller supplies the identity of the approval and the
# task token it was handed, and nothing else that matters:
#
#   {"approval_id": "...", "created_at": "...", "task_token": "...",
#    "decision": "approve" | "reject", "approver": {"user_id": "..."}, "comment": "..."}
#
# The action and its arguments are read back from the approval record, never from this
# event. The record is what a human saw and agreed to; the event is an untrusted claim
# about it. Executing anything other than the record would make the approval decorative,
# and "approve a $50 refund, execute a $5,000 one" is one edited field away.

import json
import os
import time

import boto3
from botocore.exceptions import ClientError

from agentic_trace import tracer_for
from contracts import fingerprint, require

_dynamodb = None
_lambda = None
_states = None


def handler(event, context=None):
    tracer = tracer_for(event, step="approval_executor")
    started = time.monotonic()

    fields, missing = require(event, "approval_id", "created_at", "task_token", "decision")
    if missing:
        tracer.emit("approval_callback_malformed", outcome="failure", **missing)
        tracer.flush()
        return missing

    decision = str(fields["decision"]).lower()
    if decision not in ("approve", "reject"):
        tracer.flush()
        return {
            "ok": False,
            "error": "invalid_decision",
            "expected": ["approve", "reject"],
            "received": decision,
        }

    key = {"approval_id": fields["approval_id"], "created_at": fields["created_at"]}
    approver = event.get("approver") or {}

    if decision == "reject":
        result = _reject(key, fields["task_token"], approver, event.get("comment"), tracer)
    else:
        result = _approve(key, fields["task_token"], approver, tracer)

    tracer.emit(
        "approval_resolved",
        outcome=result.get("status", "unknown"),
        latency_ms=int((time.monotonic() - started) * 1000),
        approval_id=fields["approval_id"],
        decision=decision,
    )
    tracer.flush()
    return result


def _approve(key, task_token, approver, tracer):
    # The claim is the concurrency control and the replay guard in one call. Only a record
    # still `pending` can be claimed, so a double-clicked approve button, a redelivered
    # SNS message, and a retried Lambda all collapse into one execution.
    record = _claim(key, "executing", task_token, approver)
    if record is None:
        return _already_resolved(key, tracer)

    action = record.get("action")
    arguments = _plain(record.get("arguments") or {})

    # Belt and braces: the fingerprint the validator computed over the arguments a human
    # was shown must still describe the arguments about to run.
    stored = record.get("arguments_fingerprint")
    if stored and stored != fingerprint(arguments):
        _record_outcome(key, "failed", {"error": "arguments_tampered"})
        _send_task_failure(task_token, "ApprovalTampered", "Arguments no longer match the approved proposal.")
        return {"status": "failed", "error": "arguments_tampered"}

    function_name = _write_tool_function(action)
    payload = {
        "approval_id": key["approval_id"],
        "correlation_id": record.get("correlation_id"),
        # The approval ID is the idempotency key. It is stable across every retry of this
        # execution and unique to this approved action, which is exactly the property a
        # payment provider's idempotency header needs.
        "idempotency_key": key["approval_id"],
        "arguments": arguments,
    }

    try:
        response = _lambda_client().invoke(
            FunctionName=function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload).encode("utf-8"),
        )
        body = json.loads(response["Payload"].read() or b"{}")
        failed = "FunctionError" in response or not body.get("ok", False)
    except ClientError as exc:
        body = {"error": str(exc)}
        failed = True

    if failed:
        _record_outcome(key, "failed", body)
        _send_task_failure(task_token, "WriteToolFailed", json.dumps(body)[:250])
        return {"status": "failed", "approval_id": key["approval_id"], "result": body}

    _record_outcome(key, "executed", body)
    _send_task_success(task_token, {"approval_id": key["approval_id"], "result": body})
    return {"status": "executed", "approval_id": key["approval_id"], "result": body}


def _reject(key, task_token, approver, comment, tracer):
    record = _claim(key, "rejected", task_token, approver, comment=comment)
    if record is None:
        return _already_resolved(key, tracer)

    # A rejection is a designed failure path, not an error. The state machine catches it
    # and records the rejection rather than failing the execution.
    _send_task_failure(task_token, "ApprovalRejected", comment or "Rejected by approver.")
    return {"status": "rejected", "approval_id": key["approval_id"]}


def _claim(key, new_status, task_token, approver, comment=None):
    """Moves a pending record to `new_status`, or returns None if it was not pending.

    Stamping the task token here is what ties the record to one execution: a second
    callback carrying a different token for the same approval finds the record already
    claimed and does nothing.
    """
    expression = (
        "SET #s = :new, task_token = :token, approver = :approver, resolved_at = :now"
    )
    values = {
        ":new": new_status,
        ":token": task_token,
        ":approver": approver,
        ":now": _now_iso(),
        ":pending": "pending",
    }
    if comment is not None:
        expression += ", approver_comment = :comment"
        values[":comment"] = comment

    try:
        response = _table().update_item(
            Key=key,
            UpdateExpression=expression,
            ConditionExpression="attribute_exists(approval_id) AND #s = :pending",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues=values,
            ReturnValues="ALL_NEW",
        )
        return response.get("Attributes")
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return None
        raise


def _already_resolved(key, tracer):
    """A replay, or a second approver arriving late.

    The token belonging to this approval was already resolved, so resolving it again would
    fail with TaskDoesNotExist. Report and stop — this is the correct outcome, not an
    error to retry.
    """
    current = _table().get_item(Key=key).get("Item") or {}
    tracer.emit(
        "approval_replay_ignored",
        outcome="ignored",
        approval_id=key["approval_id"],
        current_status=current.get("status", "missing"),
    )
    return {
        "status": "already_resolved",
        "approval_id": key["approval_id"],
        "current_status": current.get("status", "missing"),
    }


def _record_outcome(key, status, result):
    _table().update_item(
        Key=key,
        UpdateExpression="SET #s = :status, outcome = :outcome, completed_at = :now",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":status": status,
            ":outcome": _plain(result),
            ":now": _now_iso(),
        },
    )


def _write_tool_function(action):
    """Write tools are named <prefix><action> and the executor's IAM policy enumerates
    them individually, so a mistyped action fails as AccessDenied rather than invoking
    something unintended."""
    prefix = os.environ.get("WRITE_TOOL_PREFIX")
    if not prefix:
        raise RuntimeError("WRITE_TOOL_PREFIX is not set on the executor function.")
    return f"{prefix}{action}"


def _send_task_success(task_token, output):
    _states_client().send_task_success(
        taskToken=task_token, output=json.dumps(output, default=str)
    )


def _send_task_failure(task_token, error, cause):
    _states_client().send_task_failure(taskToken=task_token, error=error, cause=cause)


def _table():
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.resource("dynamodb").Table(os.environ["APPROVALS_TABLE"])
    return _dynamodb


def _lambda_client():
    global _lambda
    if _lambda is None:
        _lambda = boto3.client("lambda")
    return _lambda


def _states_client():
    global _states
    if _states is None:
        _states = boto3.client("stepfunctions")
    return _states


def _plain(value):
    """DynamoDB returns numbers as Decimal, which json.dumps refuses. Normalize once."""
    if isinstance(value, list):
        return [_plain(v) for v in value]
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if hasattr(value, "as_tuple"):  # decimal.Decimal
        as_int = int(value)
        return as_int if as_int == value else float(value)
    return value


def _now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
