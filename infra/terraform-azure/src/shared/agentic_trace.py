# Trace emission — PRODUCTION-PRINCIPLES.md "Log full execution traces"
#
# ---------------------------------------------------------------------------
# Why this writes to stdout, when the GCP tree calls a logging API
# ---------------------------------------------------------------------------
#
# The alerts in modules/observability all start from one KQL prelude:
#
#   let traces = FunctionAppLogs
#   | where _ResourceId has "<prefix>"
#   | extend trace = parse_json(Message)
#   | where isnotempty(trace.event_type);
#
# `FunctionAppLogs` is fed by the diagnostic setting on each function app, and its
# `Message` column is the handler's console output. So on Azure, stdout IS the pipeline —
# printing one JSON object per line is exactly right, and reaching for an SDK would put
# records somewhere the queries never look.
#
# Three consequences the rest of this file exists to enforce:
#
#   1. **One JSON object per line.** `parse_json` runs on the whole Message. A record split
#      across lines by a pretty-printer parses to null on every fragment and is dropped by
#      the `isnotempty` filter — silently, since a dropped record raises nothing.
#   2. **The field is `event_type`.** Not `event`, which is what the GCP tree uses. The KQL
#      matches `trace.event_type` literally, and the two trees genuinely differ here; a
#      handler copied from terraform-gcp/src without renaming this field emits records that
#      parse fine and match no alert.
#   3. **The terminal event is `request_complete`.** Not `execution_completed`, which is the
#      AWS and GCP name. The cost alert filters on that exact string.
#
# cost_usd and total_tokens belong on the terminal record only. Emitting them per step
# multiply-counts them against the spend alert, so this module refuses to attach them to
# anything but a terminal event.

import json
import sys
import time

# The name the daily-cost alert filters on. See point 3 above — this differs from the other
# two trees on purpose, because it is what modules/observability/main.tf actually queries.
TERMINAL_EVENT = "request_complete"

# Fields that describe a whole request, not a step within one.
_TERMINAL_ONLY = frozenset({"cost_usd", "total_tokens"})


class Tracer:
    """Collects trace records for one invocation and prints them on flush.

    Buffered rather than printed immediately so a handler that fails partway does not
    interleave its trace with a stack trace, which is how a Message column stops being
    parseable JSON.
    """

    def __init__(self, correlation_id, step=None):
        self.correlation_id = correlation_id or "unknown"
        self.default_step = step or "unknown"
        self._buffer = []

    def emit(self, event_type, **fields):
        if event_type != TERMINAL_EVENT:
            dropped = _TERMINAL_ONLY & fields.keys()
            for field in dropped:
                fields.pop(field)
            if dropped:
                fields["_dropped_terminal_fields"] = sorted(dropped)

        record = {
            # `event_type`, not `event`. modules/observability queries this exact name.
            "event_type": event_type,
            "correlation_id": self.correlation_id,
            "step": fields.pop("step", self.default_step),
            "timestamp": _now_iso(),
        }
        record.update({k: v for k, v in fields.items() if v is not None})

        self._buffer.append(record)
        return record

    def step_complete(self, outcome="success", latency_ms=None, **fields):
        return self.emit("step_complete", outcome=outcome, latency_ms=latency_ms, **fields)

    def schema_validation_failed(self, expected=None, received=None, **fields):
        """Matched by the schema-failure alert, which fires on a rising rate.

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
        """Prints each record as a single line of JSON.

        `default=str` rather than a raised TypeError: a Decimal from Cosmos or a datetime
        from an SDK response must not be the reason a trace is lost. A stringified value is
        legible; a dropped record is not.

        Never raises. An unobservable success beats a failure caused by observability.
        """
        if not self._buffer:
            return False
        try:
            for record in self._buffer:
                # separators without spaces, and no indent: one compact line, which is what
                # parse_json needs to see in the Message column.
                print(
                    json.dumps(record, default=str, separators=(",", ":")),
                    file=sys.stdout,
                    flush=True,
                )
            return True
        except Exception as exc:  # noqa: BLE001 — see the docstring
            print(f"trace_emission_failed: {exc}", file=sys.stderr)
            return False
        finally:
            self._buffer.clear()


def tracer_for(payload, step=None):
    """Builds a tracer from a request body.

    The correlation ID is the Logic App run ID, set once by the orchestrator and carried
    through every step, so a handler should never mint its own — that is how one trace
    splits into two.
    """
    correlation_id = None
    if isinstance(payload, dict):
        request = payload.get("request")
        correlation_id = (
            payload.get("correlation_id")
            or payload.get("run_id")
            or (request.get("correlation_id") if isinstance(request, dict) else None)
        )
    return Tracer(correlation_id, step=step)


def _now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
