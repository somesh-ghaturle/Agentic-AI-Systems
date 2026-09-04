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
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Callable, ClassVar

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
    arguments: dict[str, Any]
    rationale: str
    fingerprint: str

    @classmethod
    def create(cls, tool: str, arguments: dict[str, Any], rationale: str) -> WriteProposal:
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
    output: Any | None = None
    proposal: WriteProposal | None = None

    @property
    def pending(self) -> bool:
        return self.proposal is not None


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

Handler = Callable[[str, Toolbelt], Any]


@dataclass(frozen=True)
class ModelProfile:
    """A model choice with the limits the caller must enforce.

    `relative_cost` is a multiple of the cheapest tier, not a price. That is a deliberate
    change from the per-token dollar figures this held previously, and the reason is that
    those figures were wrong within a year of being written while the code around them was
    still correct — an example that teaches cost routing with stale prices teaches the
    arithmetic and misteaches the inputs.

    Ratios survive that. What a router needs to decide is whether the expensive model is
    worth it *relative* to the cheap one, and tier spacing moves far more slowly than the
    absolute numbers do. A caller that needs real prices should read them from its provider
    at runtime; this field exists to make the routing decision explainable offline.
    """

    name: str
    max_tokens: int
    relative_cost: float


class ModelRouter:
    """Select a model deterministically, without making a provider call.

    The router returns a copy of the selected profile so callers can attach it to a
    request trace or pass it to their provider adapter.  Keeping selection separate
    from invocation means this example remains offline and the approval boundary is
    unchanged.
    """

    # Anchored on Claude Sonnet 5 = 1.0. The Sonnet 5 -> Opus 5 spacing is the one ratio here
    # taken from published per-token input pricing (2026-09-03: $2 and $5 per MTok, so 2.5x).
    # The Haiku tier sits below Sonnet at 0.5, which encodes the ordering rather than quoting a
    # rate. Read these as "roughly how much more does this tier cost", never as a price.
    MODELS: ClassVar[dict[str, ModelProfile]] = {
        "simple": ModelProfile("claude-haiku-4-5", 1000, 0.5),
        "complex": ModelProfile("claude-opus-5", 4000, 2.5),
        "code": ModelProfile("claude-sonnet-5", 4000, 1.0),
    }
    _TECHNICAL_TERMS = frozenset(
        {
            "architecture",
            "debug",
            "deploy",
            "design",
            "implementation",
            "incident",
            "integration",
            "migration",
            "security",
            "terraform",
        }
    )

    def route(self, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Return the selected model profile as a plain dictionary."""
        context = context or {}
        if self._assess_complexity(query, context) > 0.8:
            profile = self.MODELS["complex"]
        elif self._is_code_request(query, context):
            profile = self.MODELS["code"]
        else:
            profile = self.MODELS["simple"]
        return {
            "name": profile.name,
            "max_tokens": profile.max_tokens,
            "relative_cost": profile.relative_cost,
        }

    def _assess_complexity(self, query: str, context: dict[str, Any]) -> float:
        """Estimate complexity from bounded, explainable request features."""
        words = query.split()
        length_score = min(len(words) / 80, 1.0)
        technical_score = min(
            len({word.lower().strip(".,:;()[]{}") for word in words} & self._TECHNICAL_TERMS)
            / 4,
            1.0,
        )
        entity_score = min(len(context.get("entities", ())) / 5, 1.0)
        file_score = min(len(context.get("files", ())) / 5, 1.0)
        explicit_score = 1.0 if any(
            marker in query.lower() for marker in ("complex", "multi-step", "step-by-step")
        ) else 0.0
        if explicit_score:
            return 1.0
        return min(
            0.2 * length_score
            + 0.25 * technical_score
            + 0.2 * entity_score
            + 0.15 * file_score
            + 0.2 * explicit_score,
            1.0,
        )

    @staticmethod
    def _is_code_request(query: str, context: dict[str, Any]) -> bool:
        if "code" in query.lower() or "program" in query.lower():
            return True
        return any(
            str(file).lower().endswith((".py", ".js", ".ts", ".go", ".rs", ".tf"))
            for file in context.get("files", ())
        )


@dataclass(frozen=True)
class Route:
    intent: str
    keywords: tuple[str, ...]
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

    def matches(self, text: str) -> str | None:
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
        self.routes: list[Route] = list(routes)
        self.fallback = fallback

    def classify(self, text: str) -> tuple[Route, str | None]:
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
    def available(self) -> list[str]:
        return self._registry.names()

    def execute(
        self, proposal: WriteProposal, token: str, tracer: Tracer | None = None
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
        approvals: ApprovalStore | None = None,
    ) -> None:
        if read_registry.access != READ:
            raise WriteBoundaryViolation(
                "Hermes must be built from the read registry; write tools belong to the "
                "approval executor"
            )
        self.router = router
        self.read_registry = read_registry
        self.approvals = approvals or ApprovalStore()

    def handle(self, request: str, tracer: Tracer | None = None) -> Result:
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
