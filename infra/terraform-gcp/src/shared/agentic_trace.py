# Trace emission — PRODUCTION-PRINCIPLES.md "Log full execution traces"
#
# The log-based metrics in modules/observability are attached to ONE log,
# projects/<project>/logs/<prefix>-traces, and they match on exact jsonPayload field names.
#
# On GCP the trap this module exists to avoid is sharper than the AWS equivalent. Anything
# a Cloud Functions handler prints to stdout is captured automatically and shows up in
# Cloud Logging looking perfectly healthy — but it lands in the function's own
# `cloudfunctions.googleapis.com/cloud-functions` log with no structured payload, so every
# metric filter misses it and every alert sits at zero. The logs are right there in the
# console, which is what makes it convincing.
#
# Two consequences this module enforces:
#
#   1. Traces go to the shared log over the Cloud Logging API, never to stdout alone.
#   2. A record missing `event` matches nothing. The filters do not approximate — note the
#      field is `event`, NOT `event_type` as on AWS, because that is what the filters in
#      modules/observability/main.tf actually match.
#
# cost_usd and total_tokens belong on the terminal record only. Emitting them per step
# multiply-counts them against the spend alert, so this module refuses to attach them to
# anything but a terminal event, and stamps `terminal: true` there because the cost metric
# filters on that field rather than on the event name.

import json
import os
import sys
import time

TERMINAL_EVENT = "execution_completed"

# Fields that describe a whole request, not a step within one.
_TERMINAL_ONLY = frozenset({"cost_usd", "total_tokens"})

_client = None
_logger = None


def _cloud_logger(log_name):
    """The Cloud Logging client, created once per container.

    Imported lazily so that a handler running in a test — or in any environment without
    google-cloud-logging installed — degrades to stdout rather than failing at import.
    """
    global _client, _logger
    if _logger is not None:
        return _logger

    from google.cloud import logging as cloud_logging  # noqa: PLC0415

    if _client is None:
        _client = cloud_logging.Client(project=os.environ.get("GCP_PROJECT"))
    _logger = _client.logger(log_name)
    return _logger


class Tracer:
    """Collects trace records for one invocation and ships them on flush.

    Buffering keeps the Logging API call off the request path for every step, and a failure
    to emit a trace never fails the request that produced it — an unobservable success is
    better than a failure caused by observability.
    """

    def __init__(self, correlation_id, log_name=None, step=None):
        self.correlation_id = correlation_id or "unknown"
        self.log_name = log_name or os.environ.get("TRACE_LOG_NAME")
        self.default_step = step or os.environ.get("K_SERVICE", "local")
        self._buffer = []

    def emit(self, event, **fields):
        if event != TERMINAL_EVENT:
            dropped = _TERMINAL_ONLY & fields.keys()
            for field in dropped:
                fields.pop(field)
            if dropped:
                fields["_dropped_terminal_fields"] = sorted(dropped)

        record = {
            # `event`, not `event_type`. modules/observability filters on this exact name.
            "event": event,
            "correlation_id": self.correlation_id,
            "step": fields.pop("step", self.default_step),
            "timestamp": _now_iso(),
        }

        # The cost metric filters on `terminal=true AND cost_usd>0` rather than on the event
        # name, so the flag has to be on the record for spend to be counted at all.
        if event == TERMINAL_EVENT:
            record["terminal"] = True

        record.update({k: v for k, v in fields.items() if v is not None})

        self._buffer.append(record)

        # Also to stdout: the function's own log is where you look when debugging this one
        # invocation, rather than querying across the whole system. It is explicitly NOT
        # where the metrics look.
        print(json.dumps(record), file=sys.stdout)
        return record

    def step_complete(self, outcome="success", latency_ms=None, **fields):
        return self.emit(
            "step_complete", outcome=outcome, latency_ms=latency_ms, **fields
        )

    def schema_validation_failed(self, expected=None, received=None, **fields):
        """Matched by the schema-failure metric, which alerts on a rising rate.

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
        if not self._buffer or not self.log_name:
            self._buffer.clear()
            return False
        try:
            logger = _cloud_logger(self.log_name)
            for record in self._buffer:
                # `severity` is what makes an entry legible in the console; the metrics
                # ignore it. json_payload is what they read.
                logger.log_struct(record, severity="INFO")
            return True
        except Exception as exc:  # noqa: BLE001 — see the class docstring
            print(
                json.dumps(
                    {
                        "event": "trace_emission_failed",
                        "correlation_id": self.correlation_id,
                        "error": str(exc),
                    }
                ),
                file=sys.stderr,
            )
            return False
        finally:
            self._buffer.clear()


def tracer_for(payload, step=None):
    """Builds a tracer from a request body.

    The correlation ID is the workflow's execution ID, set once by the orchestrator and
    carried through every step, so a handler should never mint its own — that is how a
    trace splits into two.
    """
    correlation_id = None
    if isinstance(payload, dict):
        correlation_id = (
            payload.get("execution_id")
            or payload.get("correlation_id")
            or (
                payload.get("request", {}).get("execution_id")
                if isinstance(payload.get("request"), dict)
                else None
            )
        )
    return Tracer(correlation_id, step=step)


def _now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
