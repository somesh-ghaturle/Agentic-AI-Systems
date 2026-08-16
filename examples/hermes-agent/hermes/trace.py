"""Structured trace events, one per hop.

A router is worth very little if you cannot answer "why did this request end up there".
Every decision Hermes makes emits an event carrying the same `trace_id`, so a single
request reads as an ordered story: received, classified, routed, tool called, proposed,
approved, executed.

The sink is injectable because tests assert on the event stream and the CLI prints it.
Nothing here talks to a network. Point `sink` at an OpenTelemetry span processor or a log
shipper in a real deployment; the shape below is deliberately close to what the handlers in
`infra/*/src/` already emit, so the two are greppable together.
"""

from __future__ import annotations

import json
import sys
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class Event:
    """One hop. `seq` is monotonic within a trace so ordering survives an unordered sink."""

    trace_id: str
    seq: int
    event: str
    attributes: dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0

    def to_json(self) -> str:
        return json.dumps(
            {
                "trace_id": self.trace_id,
                "seq": self.seq,
                "event": self.event,
                "timestamp": self.timestamp,
                **self.attributes,
            },
            sort_keys=True,
        )


class Tracer:
    """Collects events for one request.

    One tracer per request rather than a global: a shared mutable sequence counter across
    concurrent requests is the kind of bug that only shows up under load, and the whole
    point of the trace is to be trustworthy when something has gone wrong.
    """

    def __init__(
        self,
        trace_id: str | None = None,
        sink: Callable[[Event], None] | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.trace_id = trace_id or uuid.uuid4().hex
        self.events: list[Event] = []
        self._sink = sink
        self._clock = clock
        self._seq = 0

    def emit(self, event: str, **attributes: Any) -> Event:
        self._seq += 1
        record = Event(
            trace_id=self.trace_id,
            seq=self._seq,
            event=event,
            attributes=attributes,
            timestamp=self._clock(),
        )
        self.events.append(record)
        if self._sink is not None:
            self._sink(record)
        return record

    def event_names(self) -> list[str]:
        return [event.event for event in self.events]


def stdout_sink(event: Event) -> None:
    """Print one JSON object per line. Stderr, so piping the CLI's answer stays clean."""
    print(event.to_json(), file=sys.stderr)
