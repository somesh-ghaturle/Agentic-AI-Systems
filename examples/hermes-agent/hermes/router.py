"""The router, the handlers it dispatches to, and the executor that is the only way to write.

Hermes is a courier, not an oracle. It takes a request, decides which handler owns it, and
carries it there. The interesting part is not the classification — it is that the courier
has no authority of its own. Read work runs on the spot; anything that changes state comes
back as a `WriteProposal` and stops there.

Classification here is ordered keyword rules, which is a deliberate choice rather than a
placeholder. Routing is the step you most want to be able to explain after the fact, and a
rule that fired is explainable in a way that a model's judgement is not. Swap
`Router.classify` for a model call when the intents stop being separable by vocabulary —
the return type is the seam, and everything downstream is unchanged.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from .approvals import ApprovalStore, fingerprint
from .tools import (
    READ,
    WRITE,
    Toolbelt,
    ToolRegistry,
    WriteBoundaryViolation,
)
from .trace import Tracer

# ---------------------------------------------------------------------------
# What comes back
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WriteProposal:
    """A handler's request to change something. Inert until approved.

    It carries the fingerprint so that whoever displays it to a human is displaying the
    same bytes that the executor will later check. A UI that renders a friendly summary and
    an executor that checks something else is how approval systems end up approving one
    thing and doing another.
    """

    tool: str
    arguments: Dict[str, Any]
    rationale: str
    fingerprint: str

    @classmethod
    def create(cls, tool: str, arguments: Dict[str, Any], rationale: str) -> "WriteProposal":
        arguments = dict(arguments)
        return cls(
            tool=tool,
            arguments=arguments,
            rationale=rationale,
            fingerprint=fingerprint(tool, arguments),
        )


@dataclass(frozen=True)
class Result:
    """What `Hermes.handle` returns.

    `pending` is not an error state and not a failure. It is the system working: the
    request was understood, routed, and stopped at the boundary on purpose.
    """

    trace_id: str
    intent: str
    handler: str
    output: Optional[Any] = None
    proposal: Optional[WriteProposal] = None

    @property
    def pending(self) -> bool:
        return self.proposal is not None


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

Handler = Callable[[str, Toolbelt], Any]


@dataclass(frozen=True)
class Route:
    intent: str
    keywords: Tuple[str, ...]
    handler: Handler
    description: str = ""

    def __post_init__(self) -> None:
        # Word boundaries, not substrings. `"is" in "summarize this incident"` is true —
        # it is inside "th(is)" — and a router built on `in` will send that request to a
        # status handler and log a confident reason for doing so. Misrouting on a substring
        # of an unrelated word is the failure this class exists to not have.
        object.__setattr__(
            self,
            "_patterns",
            tuple(
                (keyword, re.compile(r"\b" + re.escape(keyword) + r"\b", re.IGNORECASE))
                for keyword in self.keywords
            ),
        )

    def matches(self, text: str) -> Optional[str]:
        """Return the keyword that fired, so the trace can say *why* this route won."""
        for keyword, pattern in self._patterns:  # type: ignore[attr-defined]
            if pattern.search(text):
                return keyword
        return None


class Router:
    """Ordered rules, first match wins, explicit fallback.

    Order is significant and that is the point: "delete the cached search index" contains
    both `search` and `delete`, and which one wins is a policy decision. Put the
    consequential intents first so an ambiguous request lands on the path that asks a human
    rather than the one that answers immediately.
    """

    def __init__(self, routes: Sequence[Route], fallback: Route) -> None:
        self.routes: List[Route] = list(routes)
        self.fallback = fallback

    def classify(self, text: str) -> Tuple[Route, Optional[str]]:
        for route in self.routes:
            keyword = route.matches(text)
            if keyword is not None:
                return route, keyword
        return self.fallback, None


# ---------------------------------------------------------------------------
# The executor — the only object holding write callables
# ---------------------------------------------------------------------------


class ApprovalExecutor:
    """Runs an approved write. Nothing else in this package can run one.

    Two locks, either sufficient on its own:

      1. It refuses a proposal whose approval does not claim cleanly for those exact
         arguments.
      2. It is the only holder of the write registry. `Hermes` never receives it, so there
         is no reference to reach even with the check removed.

    It also refuses to run a *read* tool. That looks like pedantry and is not: if the
    executor accepted read tools, a future refactor could route everything through it "for
    consistency", and the two paths would collapse into one with an approval check that
    most calls skip.
    """

    def __init__(
        self,
        write_registry: ToolRegistry,
        approvals: ApprovalStore,
    ) -> None:
        if write_registry.access != WRITE:
            raise WriteBoundaryViolation(
                "the approval executor must be built from the write registry"
            )
        self._registry = write_registry
        self._approvals = approvals

    @property
    def available(self) -> List[str]:
        return self._registry.names()

    def execute(
        self, proposal: WriteProposal, token: str, tracer: Optional[Tracer] = None
    ) -> Any:
        tool = self._registry.get(proposal.tool)
        if tool.access != WRITE:
            raise WriteBoundaryViolation(
                f"tool {proposal.tool!r} is {tool.access!r}; the approval executor runs "
                "write tools only"
            )
        # Claim before running. A claim that happened after the side effect would let a
        # crash between the two leave the action done and the token still spendable.
        approval = self._approvals.claim(token, proposal.tool, proposal.arguments)
        if tracer is not None:
            tracer.emit(
                "approval.claimed",
                tool=proposal.tool,
                approver=approval.approver,
                fingerprint=proposal.fingerprint,
            )
            tracer.emit(
                "tool.call",
                tool=proposal.tool,
                access=WRITE,
                arguments=proposal.arguments,
            )
        result = tool.run(dict(proposal.arguments))
        if tracer is not None:
            tracer.emit("tool.result", tool=proposal.tool, access=WRITE)
        return result


# ---------------------------------------------------------------------------
# The agent
# ---------------------------------------------------------------------------


class Hermes:
    """The dispatcher.

    Holds the read registry, the router, and the approval store. It does not hold the write
    registry — that lives in `ApprovalExecutor`, and the separation is the design rather
    than an implementation detail. `test_hermes_agent.py` asserts it structurally, because
    a comment saying "do not add this" is not a control.
    """

    def __init__(
        self,
        router: Router,
        read_registry: ToolRegistry,
        approvals: Optional[ApprovalStore] = None,
    ) -> None:
        if read_registry.access != READ:
            raise WriteBoundaryViolation(
                "Hermes must be built from the read registry; write tools belong to the "
                "approval executor"
            )
        self.router = router
        self.read_registry = read_registry
        self.approvals = approvals or ApprovalStore()

    def handle(self, request: str, tracer: Optional[Tracer] = None) -> Result:
        tracer = tracer or Tracer()
        tracer.emit("request.received", characters=len(request))

        route, keyword = self.router.classify(request)
        tracer.emit(
            "request.classified",
            intent=route.intent,
            matched=keyword,
            fallback=keyword is None,
        )

        toolbelt = Toolbelt(self.read_registry, tracer=tracer)
        tracer.emit(
            "request.routed", intent=route.intent, tools_available=toolbelt.available
        )

        outcome = route.handler(request, toolbelt)

        if isinstance(outcome, WriteProposal):
            tracer.emit(
                "write.proposed",
                tool=outcome.tool,
                arguments=outcome.arguments,
                fingerprint=outcome.fingerprint,
            )
            return Result(
                trace_id=tracer.trace_id,
                intent=route.intent,
                handler=route.handler.__name__,
                proposal=outcome,
            )

        tracer.emit("request.completed", intent=route.intent)
        return Result(
            trace_id=tracer.trace_id,
            intent=route.intent,
            handler=route.handler.__name__,
            output=outcome,
        )
