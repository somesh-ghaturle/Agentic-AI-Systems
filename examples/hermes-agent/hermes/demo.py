"""A wired-up Hermes with simulated tools, so the example runs with nothing installed.

Every tool here returns canned data. That is on purpose: the subject of this example is
the boundary and the routing, and a tool that needs an API key is a tool that stops the
example from running in CI. Replace the bodies with real calls and nothing above them
changes — which is itself the claim being demonstrated.
"""

from __future__ import annotations

import re
from typing import Any

from .approvals import ApprovalStore
from .router import ApprovalExecutor, Hermes, Route, Router, WriteProposal
from .tools import READ, WRITE, Tool, Toolbelt, ToolRegistry

# ---------------------------------------------------------------------------
# Simulated tools
# ---------------------------------------------------------------------------

_KNOWLEDGE_BASE = {
    "incident-2291": (
        "Checkout latency rose to 4.2s at 02:10 UTC. Cause: connection pool exhaustion "
        "in the billing service after a deploy. Mitigated by a restart at 02:41 UTC."
    ),
    "runbook-billing": (
        "Billing service runbook: check pool saturation first, then upstream payment "
        "provider latency. Restart is safe and takes about 40 seconds."
    ),
    "postmortem-template": "Summary, impact, timeline, root cause, action items, owners.",
}

_SERVICE_STATE = {
    "billing": {"healthy": True, "version": "2.14.1", "restarts_today": 1},
    "checkout": {"healthy": True, "version": "5.0.3", "restarts_today": 0},
    "payments": {"healthy": False, "version": "1.9.9", "restarts_today": 3},
}


def _kb_search(arguments: dict[str, Any]) -> dict[str, Any]:
    query = str(arguments.get("query", "")).lower()
    hits = [
        key
        for key, text in _KNOWLEDGE_BASE.items()
        if query and (query in key.lower() or query in text.lower())
    ]
    return {"query": arguments.get("query", ""), "hits": hits or sorted(_KNOWLEDGE_BASE)[:2]}


def _fetch_document(arguments: dict[str, Any]) -> dict[str, Any]:
    key = str(arguments.get("id", ""))
    return {"id": key, "text": _KNOWLEDGE_BASE.get(key, "(no such document)")}


def _service_status(arguments: dict[str, Any]) -> dict[str, Any]:
    name = str(arguments.get("service", ""))
    return {"service": name, "status": _SERVICE_STATE.get(name, {"healthy": None})}


def _restart_service(arguments: dict[str, Any]) -> dict[str, Any]:
    name = str(arguments.get("service", ""))
    state = _SERVICE_STATE.setdefault(
        name, {"healthy": True, "version": "0.0.0", "restarts_today": 0}
    )
    state["restarts_today"] += 1
    state["healthy"] = True
    return {"restarted": name, "restarts_today": state["restarts_today"]}


def _post_message(arguments: dict[str, Any]) -> dict[str, Any]:
    return {
        "posted_to": arguments.get("channel", ""),
        "characters": len(str(arguments.get("body", ""))),
    }


def _delete_record(arguments: dict[str, Any]) -> dict[str, Any]:
    return {"deleted": arguments.get("id", ""), "recoverable": False}


def build_registries() -> tuple[ToolRegistry, ToolRegistry]:
    read = ToolRegistry(READ)
    read.register(Tool("kb_search", READ, "Search the internal knowledge base", _kb_search))
    read.register(Tool("fetch_document", READ, "Fetch one document by id", _fetch_document))
    read.register(Tool("service_status", READ, "Read a service's health", _service_status))

    write = ToolRegistry(WRITE)
    write.register(Tool("restart_service", WRITE, "Restart a service", _restart_service))
    write.register(Tool("post_message", WRITE, "Post to a channel", _post_message))
    write.register(Tool("delete_record", WRITE, "Delete a record", _delete_record))
    return read, write


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def research(request: str, tools: Toolbelt) -> dict[str, Any]:
    """Search, then read the top hit. Two read calls, no approval needed for either."""
    found = tools.call("kb_search", {"query": _subject(request) or request})
    documents = [tools.call("fetch_document", {"id": hit}) for hit in found["hits"][:2]]
    return {
        "answer": " ".join(document["text"] for document in documents),
        "sources": [document["id"] for document in documents],
    }


def status(request: str, tools: Toolbelt) -> dict[str, Any]:
    service = _service_name(request) or "billing"
    return tools.call("service_status", {"service": service})


def act(request: str, tools: Toolbelt) -> WriteProposal:
    """Decide what to change, read enough to justify it, then stop.

    Note the read call: the handler still gathers context, and the proposal it returns
    carries a rationale drawn from it. Stopping at the boundary does not mean stopping at
    the first sign of work — a human approving a blank action is approving nothing.
    """
    if "delete" in request.lower():
        return WriteProposal.create(
            "delete_record",
            {"id": _subject(request) or "unknown"},
            rationale="Request asked for a deletion; deletions are not recoverable.",
        )
    if "post" in request.lower() or "notify" in request.lower() or "announce" in request.lower():
        return WriteProposal.create(
            "post_message",
            {"channel": "#incidents", "body": request},
            rationale="Request asked to notify a channel.",
        )

    service = _service_name(request) or "billing"
    current = tools.call("service_status", {"service": service})
    healthy = current["status"].get("healthy")
    return WriteProposal.create(
        "restart_service",
        {"service": service},
        rationale=(
            f"Service {service!r} reports healthy={healthy}; a restart clears the "
            "connection pool and takes about 40 seconds."
        ),
    )


def unrouted(request: str, tools: Toolbelt) -> dict[str, Any]:
    """The fallback says so plainly instead of guessing.

    A router that quietly picks its most common route when it does not understand
    something is a router whose traces stop meaning anything.
    """
    return {
        "answer": "No route matched this request.",
        "tools_available": tools.available,
    }


# ---------------------------------------------------------------------------
# Wiring
# ---------------------------------------------------------------------------

# Order matters. The write-bearing intent is first so that a request mentioning both a
# lookup and a change ("find the stale records and delete them") lands on the path that
# asks a human rather than the one that answers on its own.
ROUTES = (
    Route(
        intent="act",
        keywords=("restart", "delete", "deploy", "post", "notify", "announce", "roll back"),
        handler=act,
        description="Anything that changes state. Always returns a proposal.",
    ),
    Route(
        intent="status",
        keywords=("status", "health", "healthy", "up"),
        handler=status,
        description="Read a service's current health.",
    ),
    Route(
        intent="research",
        keywords=("search", "find", "look up", "summarize", "summarise", "what", "why", "how"),
        handler=research,
        description="Knowledge-base retrieval and summarisation.",
    ),
)

FALLBACK = Route(intent="unrouted", keywords=(), handler=unrouted)


def build_agent(
    approvals: ApprovalStore | None = None,
) -> tuple[Hermes, ApprovalExecutor]:
    """Return the pair. They share an approval store and nothing else.

    Returning two objects rather than one with an `execute_write` method is the point: the
    caller can hand `Hermes` to whatever accepts requests and keep the executor behind
    whatever gates approvals.
    """
    read_registry, write_registry = build_registries()
    approvals = approvals or ApprovalStore()
    agent = Hermes(Router(ROUTES, FALLBACK), read_registry, approvals)
    executor = ApprovalExecutor(write_registry, approvals)
    return agent, executor


# ---------------------------------------------------------------------------
# Crude argument extraction — deliberately crude
# ---------------------------------------------------------------------------

_SERVICE_PATTERN = re.compile(
    r"\b(" + "|".join(sorted(_SERVICE_STATE, key=len, reverse=True)) + r")\b", re.IGNORECASE
)
_ID_PATTERN = re.compile(r"\b([a-z]+-[a-z0-9]+)\b", re.IGNORECASE)


def _service_name(request: str) -> str | None:
    match = _SERVICE_PATTERN.search(request)
    return match.group(1).lower() if match else None


def _subject(request: str) -> str | None:
    """Pull an identifier like `incident-2291` out of the text.

    A real system takes structured arguments from a model's tool call rather than guessing
    from prose. This exists so the demo has something to fingerprint, and it is worth being
    honest that argument extraction is where a router most easily gets an approval bound to
    the wrong thing.
    """
    match = _ID_PATTERN.search(request)
    return match.group(1).lower() if match else None
