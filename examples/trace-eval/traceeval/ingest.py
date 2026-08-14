"""Turn a stream of JSON lines into traces you can ask questions of.

The harness deliberately consumes a *serialised* trace rather than in-process objects. That
is what makes it an eval harness and not a test suite: it can score a run that happened
last week, in another process, on a system nobody here wrote. The only contract is the
event shape — `trace_id`, `seq`, `event`, and whatever attributes that event carries.

Malformed input is normal, not exceptional. A trace arrives truncated because the process
died, or with a gap because a log shipper dropped a line. Those are findings about the run,
not reasons to crash the harness, so parsing collects problems instead of raising.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

REQUIRED_KEYS = ("trace_id", "seq", "event")


@dataclass(frozen=True)
class Event:
    trace_id: str
    seq: int
    event: str
    attributes: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.attributes.get(key, default)


@dataclass
class Trace:
    trace_id: str
    events: List[Event] = field(default_factory=list)
    parse_errors: List[str] = field(default_factory=list)

    def named(self, name: str) -> List[Event]:
        return [event for event in self.events if event.event == name]

    def first(self, name: str) -> Optional[Event]:
        for event in self.events:
            if event.event == name:
                return event
        return None

    def last(self, name: str) -> Optional[Event]:
        found = self.named(name)
        return found[-1] if found else None

    def names(self) -> List[str]:
        return [event.event for event in self.events]

    @property
    def intent(self) -> Optional[str]:
        classified = self.first("request.classified")
        return classified.get("intent") if classified else None

    def tool_calls(self, access: Optional[str] = None) -> List[Event]:
        calls = self.named("tool.call")
        if access is None:
            return calls
        return [call for call in calls if call.get("access") == access]


def parse_line(line: str) -> Any:
    """Return an `Event`, or a string describing why the line is not one."""
    line = line.strip()
    if not line:
        return None
    try:
        payload = json.loads(line)
    except json.JSONDecodeError as error:
        return f"line is not JSON: {error.msg}"
    if not isinstance(payload, dict):
        return f"line is JSON but not an object: {type(payload).__name__}"
    missing = [key for key in REQUIRED_KEYS if key not in payload]
    if missing:
        return f"event is missing {', '.join(missing)}"
    try:
        seq = int(payload["seq"])
    except (TypeError, ValueError):
        return f"seq is not an integer: {payload['seq']!r}"
    attributes = {
        key: value for key, value in payload.items() if key not in REQUIRED_KEYS
    }
    return Event(
        trace_id=str(payload["trace_id"]),
        seq=seq,
        event=str(payload["event"]),
        attributes=attributes,
    )


def load(lines: Iterable[str]) -> List[Trace]:
    """Group lines into traces, ordered by `seq`.

    Sorting by `seq` rather than trusting arrival order is the point of carrying a sequence
    number at all — any sink that fans out or batches will reorder, and a harness that
    inferred ordering from position would report imaginary out-of-order bugs on a system
    that is fine.
    """
    traces: Dict[str, Trace] = {}
    orphan_errors: List[str] = []

    for number, line in enumerate(lines, 1):
        parsed = parse_line(line)
        if parsed is None:
            continue
        if isinstance(parsed, str):
            orphan_errors.append(f"line {number}: {parsed}")
            continue
        trace = traces.setdefault(parsed.trace_id, Trace(trace_id=parsed.trace_id))
        trace.events.append(parsed)

    for trace in traces.values():
        trace.events.sort(key=lambda event: event.seq)

    ordered = list(traces.values())
    if orphan_errors:
        # Unparseable lines carry no trace_id, so they cannot be filed under one. Attaching
        # them to every trace would be a lie; dropping them silently would hide a broken
        # producer. They go on the first trace, and `parse_errors` says how many.
        if ordered:
            ordered[0].parse_errors.extend(orphan_errors)
        else:
            ordered.append(Trace(trace_id="(unparseable)", parse_errors=orphan_errors))
    return ordered


def load_one(lines: Iterable[str]) -> Trace:
    """For the common case of a single request's trace. Raises if the stream holds more."""
    traces = load(lines)
    if not traces:
        raise ValueError("no events in stream")
    if len(traces) > 1:
        raise ValueError(
            f"expected one trace, found {len(traces)}: {[t.trace_id for t in traces]}"
        )
    return traces[0]
