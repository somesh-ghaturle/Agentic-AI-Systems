"""The two systems under evaluation.

Both answer the same requests using the *same tools over the same data* — the write tools
are literally the functions from the Hermes example, not reimplementations. Only the
architecture differs. That is what makes the comparison mean anything: when the outputs
match and the traces do not, the difference is the boundary and nothing else.

  `hermes`  — the router from `examples/hermes-agent`. Read tools run on the spot; a write
              comes back as a proposal and the run stops there.

  `naive`   — the same job done the obvious way. One registry, no split, handlers call
              whatever they like. It is not a strawman: it is what an agent looks like
              before anyone draws the boundary, and it produces good answers.

The eval harness itself imports neither. It receives a rendered answer and a list of JSON
lines, which is all it would get from a system running in another process last week.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

HERMES = Path(__file__).resolve().parents[2] / "hermes-agent"
if not (HERMES / "hermes" / "__init__.py").exists():
    raise ImportError(
        f"expected the Hermes example at {HERMES}. This harness evaluates it; see "
        "examples/hermes-agent/README.md"
    )
sys.path.insert(0, str(HERMES))

from hermes import Tracer  # noqa: E402
from hermes.demo import _service_name, _subject, build_agent, build_registries  # noqa: E402


@dataclass
class Run:
    """What a subject hands the graders: the text a user sees, and the trace."""

    case: Any
    subject: str
    answer: str
    trace_lines: list[str] = field(default_factory=list)


def _render(value: Any) -> str:
    return value if isinstance(value, str) else json.dumps(value, sort_keys=True)


# ---------------------------------------------------------------------------
# Subject 1 — Hermes
# ---------------------------------------------------------------------------


def run_hermes(case) -> Run:
    lines: list[str] = []
    agent, _executor = build_agent()
    tracer = Tracer(sink=lambda event: lines.append(event.to_json()))
    result = agent.handle(case.request, tracer=tracer)

    if result.pending:
        proposal = result.proposal
        arguments = ", ".join(
            f"{key}={value!r}" for key, value in sorted(proposal.arguments.items())
        )
        answer = (
            f"Awaiting approval to run {proposal.tool}({arguments}). {proposal.rationale}"
        )
    else:
        answer = _render(result.output)

    return Run(case=case, subject="hermes", answer=answer, trace_lines=lines)


# ---------------------------------------------------------------------------
# Subject 2 — the same job, done the obvious way
# ---------------------------------------------------------------------------

_NAIVE_ROUTES = (
    ("act", ("restart", "delete", "deploy", "post", "notify", "announce")),
    ("status", ("status", "health", "healthy", "is ", "up")),
    ("research", ("search", "find", "look up", "summarize", "what", "why", "how")),
)


def _naive_classify(request: str):
    """Substring matching, because that is what you write first.

    `"is " in "summarize this incident"` is true. The bug is not exotic and not the
    author's fault — it is what `in` does.
    """
    lowered = request.lower()
    for intent, keywords in _NAIVE_ROUTES:
        for keyword in keywords:
            if keyword in lowered:
                return intent, keyword
    return "unrouted", None


def run_naive(case) -> Run:
    lines: list[str] = []
    tracer = Tracer(sink=lambda event: lines.append(event.to_json()))

    read_registry, write_registry = build_registries()
    # One table. Nothing here knows the difference between reading and writing.
    tools: dict[str, Any] = {}
    for registry in (read_registry, write_registry):
        for name in registry.names():
            tools[name] = registry.get(name)

    def call(name: str, arguments: dict[str, Any]) -> Any:
        tool = tools[name]
        tracer.emit("tool.call", tool=name, access=tool.access, arguments=arguments)
        result = tool.run(dict(arguments))
        tracer.emit("tool.result", tool=name, access=tool.access)
        return result

    tracer.emit("request.received", characters=len(case.request))
    intent, keyword = _naive_classify(case.request)
    tracer.emit(
        "request.classified", intent=intent, matched=keyword, fallback=keyword is None
    )
    tracer.emit("request.routed", intent=intent, tools_available=sorted(tools))

    output = _naive_handle(intent, case.request, call)
    tracer.emit("request.completed", intent=intent)
    return Run(
        case=case, subject="naive", answer=_render(output), trace_lines=lines
    )


def _naive_handle(intent: str, request: str, call: Callable) -> Any:
    if intent == "research":
        found = call("kb_search", {"query": _subject(request) or request})
        documents = [call("fetch_document", {"id": hit}) for hit in found["hits"][:2]]
        return {
            "answer": " ".join(document["text"] for document in documents),
            "sources": [document["id"] for document in documents],
        }

    if intent == "status":
        return call("service_status", {"service": _service_name(request) or "billing"})

    if intent == "act":
        lowered = request.lower()
        if "delete" in lowered:
            return call("delete_record", {"id": _subject(request) or "unknown"})
        if any(word in lowered for word in ("post", "notify", "announce")):
            return call("post_message", {"channel": "#incidents", "body": request})

        service = _service_name(request) or "billing"
        # Check, then check again before acting. Harmless-looking, and it doubles the reads
        # on every action the system takes.
        call("service_status", {"service": service})
        call("service_status", {"service": service})
        return call("restart_service", {"service": service})

    return {"answer": "No route matched this request.", "tools_available": []}


SUBJECTS: dict[str, Callable[[Any], Run]] = {
    "hermes": run_hermes,
    "naive": run_naive,
}
