# Trace emission — PRODUCTION-PRINCIPLES.md "Log full execution traces"
#
# The metric filters in modules/observability are attached to ONE log group,
# /agentic/<prefix>/traces, and they match on exact JSON field names. Two consequences
# that this module exists to enforce:
#
#   1. Writing to the handler's own /aws/lambda/... group is invisible to every alarm.
#      Traces go to the shared group, over the Logs API.
#   2. A record missing `event_type` or `cost_usd` matches nothing. The filters do not
#      approximate.
#
# cost_usd and total_tokens belong on the terminal record only. Emitting them per step
# multiply-counts them against the daily cost alarm, so this module refuses to attach
# them to anything but a terminal event.

import json
import os
import sys
import time
import uuid

import boto3
from botocore.exceptions import ClientError

TERMINAL_EVENT = "request_complete"

# Fields that describe a whole request, not a step within one.
_TERMINAL_ONLY = frozenset({"cost_usd", "total_tokens"})

_logs_client = None
_stream_name = None


def _client():
    global _logs_client
    if _logs_client is None:
        _logs_client = boto3.client("logs")
    return _logs_client


def _stream(log_group):
    """One stream per container, created lazily and reused across invocations."""
    global _stream_name
    if _stream_name is not None:
        return _stream_name

    function = os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "local")
    candidate = f"{time.strftime('%Y/%m/%d')}/{function}/{uuid.uuid4().hex}"
    try:
        _client().create_log_stream(logGroupName=log_group, logStreamName=candidate)
    except ClientError as exc:
        if exc.response["Error"]["Code"] != "ResourceAlreadyExistsException":
            raise
    _stream_name = candidate
    return _stream_name


class Tracer:
    """Collects trace records for one invocation and ships them on flush.

    Buffering keeps the Logs API call off the request path for every step, and a failure
    to emit a trace never fails the request that produced it — an unobservable success is
    better than a failure caused by observability.
    """

    def __init__(self, correlation_id, log_group=None, step=None):
        self.correlation_id = correlation_id or "unknown"
        self.log_group = log_group or os.environ.get("TRACE_LOG_GROUP")
        self.default_step = step or os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "local")
        self._buffer = []

    def emit(self, event_type, **fields):
        if event_type != TERMINAL_EVENT:
            dropped = _TERMINAL_ONLY & fields.keys()
            for field in dropped:
                fields.pop(field)
            if dropped:
                fields["_dropped_terminal_fields"] = sorted(dropped)

        record = {
            "event_type": event_type,
            "correlation_id": self.correlation_id,
            "step": fields.pop("step", self.default_step),
            "timestamp": _now_iso(),
        }
        record.update({k: v for k, v in fields.items() if v is not None})

        self._buffer.append((int(time.time() * 1000), record))

        # Also to stdout: the function's own log group is where you look when debugging
        # this one invocation, rather than querying across the whole system.
        print(json.dumps(record), file=sys.stdout)
        return record

    def step_complete(self, outcome="success", latency_ms=None, **fields):
        return self.emit(
            "step_complete", outcome=outcome, latency_ms=latency_ms, **fields
        )

    def schema_validation_failed(self, expected=None, received=None, **fields):
        """Matched by the schema-failure filter, which alarms on a rising rate.

        A model that has drifted off its output contract shows up here first, usually
        before anyone reports a symptom.
        """
        return self.emit(
            "schema_validation_failed", expected=expected, received=received, **fields
        )

    def terminal(self, outcome, total_tokens=None, cost_usd=None, **fields):
        return self.emit(
            TERMINAL_EVENT,
            outcome=outcome,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            **fields,
        )

    def flush(self):
        if not self._buffer or not self.log_group:
            self._buffer.clear()
            return False
        try:
            _client().put_log_events(
                logGroupName=self.log_group,
                logStreamName=_stream(self.log_group),
                logEvents=[
                    {"timestamp": ts, "message": json.dumps(rec)}
                    for ts, rec in sorted(self._buffer, key=lambda item: item[0])
                ],
            )
            return True
        except ClientError as exc:
            print(
                json.dumps(
                    {
                        "event_type": "trace_emission_failed",
                        "correlation_id": self.correlation_id,
                        "error": str(exc),
                    }
                ),
                file=sys.stderr,
            )
            return False
        finally:
            self._buffer.clear()


def tracer_for(event, step=None):
    """Builds a tracer from a state machine payload.

    The correlation ID is set once by the orchestrator and carried through every state, so
    a handler should never mint its own — that is how a trace splits into two.
    """
    correlation_id = None
    if isinstance(event, dict):
        correlation_id = event.get("correlation_id") or (
            event.get("request", {}).get("correlation_id")
            if isinstance(event.get("request"), dict)
            else None
        )
    return Tracer(correlation_id, step=step)


def _now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
