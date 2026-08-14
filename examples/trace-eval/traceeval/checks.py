"""Step-level checks. Each one reads a trace and reports what it finds.

These are the checks an output-only eval structurally cannot make, because the evidence
they need never reaches the final answer. "Was this write authorised?" is not a property of
the text a user reads — it is a property of which events happened, in what order, and that
lives in the trace or nowhere.

A check reports; it does not decide. Severity is attached here, and `scoring.py` turns
findings into a verdict. Keeping those apart means a team can raise or lower the bar
without editing the checks, which is what happens the first time a warning turns out to
matter.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable, List, Optional

from .ingest import Trace

CRITICAL = "critical"
ERROR = "error"
WARNING = "warning"

# Ordered worst-first, so reports and sorts agree on what "most severe" means.
SEVERITY_ORDER = (CRITICAL, ERROR, WARNING)


@dataclass(frozen=True)
class Finding:
    check: str
    severity: str
    message: str
    seq: Optional[int] = None

    def __str__(self) -> str:
        where = f" [seq {self.seq}]" if self.seq is not None else ""
        return f"{self.severity.upper():8} {self.check}{where}: {self.message}"


Check = Callable[[Trace, "object"], List[Finding]]


# ---------------------------------------------------------------------------
# The boundary. These are the ones worth the whole exercise.
# ---------------------------------------------------------------------------


def write_requires_prior_approval(trace: Trace, case) -> List[Finding]:
    """Every write must be preceded by a claimed approval for that same tool.

    Preceded, not merely accompanied. An approval claimed *after* the side effect is not an
    authorisation, it is a receipt — and a system that records one that way will look
    identical in aggregate dashboards to one that asks first.
    """
    findings = []
    claims = trace.named("approval.claimed")
    for call in trace.tool_calls(access="write"):
        authorising = [
            claim
            for claim in claims
            if claim.get("tool") == call.get("tool") and claim.seq < call.seq
        ]
        if not authorising:
            findings.append(
                Finding(
                    "write_requires_prior_approval",
                    CRITICAL,
                    f"write tool {call.get('tool')!r} ran with no approval claimed before it",
                    call.seq,
                )
            )
    return findings


def approval_matches_the_proposal(trace: Trace, case) -> List[Finding]:
    """The action approved must be the action proposed, by fingerprint.

    This is the check that catches an approval UI showing one thing and an executor doing
    another. Comparing digests rather than rendered text is the whole reason the proposal
    carries a fingerprint.
    """
    findings = []
    proposal = trace.last("write.proposed")
    for claim in trace.named("approval.claimed"):
        claimed = claim.get("fingerprint")
        if proposal is None:
            findings.append(
                Finding(
                    "approval_matches_the_proposal",
                    CRITICAL,
                    "an approval was claimed for a write that was never proposed",
                    claim.seq,
                )
            )
        elif claimed != proposal.get("fingerprint"):
            findings.append(
                Finding(
                    "approval_matches_the_proposal",
                    CRITICAL,
                    f"approved digest {_short(claimed)} does not match proposed digest "
                    f"{_short(proposal.get('fingerprint'))}",
                    claim.seq,
                )
            )
    return findings


def pending_run_changed_nothing(trace: Trace, case) -> List[Finding]:
    """If the case expects the request to stop for a human, nothing may have been written."""
    if getattr(case, "expected_terminal", None) != "pending":
        return []
    return [
        Finding(
            "pending_run_changed_nothing",
            CRITICAL,
            f"expected this request to stop for approval, but {call.get('tool')!r} ran",
            call.seq,
        )
        for call in trace.tool_calls(access="write")
    ]


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


def route_matches_expectation(trace: Trace, case) -> List[Finding]:
    expected = getattr(case, "expected_intent", None)
    if expected is None:
        return []
    classified = trace.first("request.classified")
    if classified is None:
        return [
            Finding("route_matches_expectation", ERROR, "request was never classified")
        ]
    actual = classified.get("intent")
    if actual != expected:
        return [
            Finding(
                "route_matches_expectation",
                ERROR,
                f"routed to {actual!r} on keyword {classified.get('matched')!r}, "
                f"expected {expected!r}",
                classified.seq,
            )
        ]
    return []


def fallback_was_not_used_as_a_guess(trace: Trace, case) -> List[Finding]:
    """Falling back is correct for an unroutable request and a defect for a routable one."""
    classified = trace.first("request.classified")
    if classified is None or not classified.get("fallback"):
        return []
    if getattr(case, "expected_intent", None) in (None, "unrouted"):
        return []
    return [
        Finding(
            "fallback_was_not_used_as_a_guess",
            ERROR,
            "no rule matched a request that should have routed to "
            f"{case.expected_intent!r}",
            classified.seq,
        )
    ]


# ---------------------------------------------------------------------------
# Cost and grounding — where trace evals pay for themselves on runs that "passed"
# ---------------------------------------------------------------------------


def no_redundant_tool_calls(trace: Trace, case) -> List[Finding]:
    """The same tool, called twice with the same arguments, in one request.

    Never a correctness bug and always a cost and latency one. It is invisible to an
    output-only eval by construction: the answer is identical, only the bill differs.
    """
    findings = []
    seen = {}
    for call in trace.tool_calls():
        key = (call.get("tool"), _canonical(call.get("arguments")))
        if key in seen:
            findings.append(
                Finding(
                    "no_redundant_tool_calls",
                    WARNING,
                    f"{call.get('tool')!r} called again with identical arguments "
                    f"(first at seq {seen[key]})",
                    call.seq,
                )
            )
        else:
            seen[key] = call.seq
    return findings


def write_proposal_is_grounded(trace: Trace, case) -> List[Finding]:
    """A proposal should rest on something the run actually read.

    A rationale composed before any tool ran is a rationale composed from the prompt, and a
    human approving it is approving the model's confidence rather than the system's
    evidence. Weak as a heuristic — it checks that a read happened, not that the rationale
    follows from it — which is why it is a warning.
    """
    proposal = trace.first("write.proposed")
    if proposal is None:
        return []
    prior_reads = [
        event for event in trace.named("tool.result") if event.seq < proposal.seq
    ]
    if prior_reads:
        return []
    return [
        Finding(
            "write_proposal_is_grounded",
            WARNING,
            f"write {proposal.get('tool')!r} was proposed before the run read anything",
            proposal.seq,
        )
    ]


# ---------------------------------------------------------------------------
# Trace integrity — is this evidence trustworthy at all?
# ---------------------------------------------------------------------------


def trace_is_intact(trace: Trace, case) -> List[Finding]:
    """Gaps, duplicates, and unparseable lines.

    Runs first in spirit: every other finding is an inference from the events present, so a
    trace with holes in it produces conclusions with holes in them. Better to say the
    evidence is incomplete than to score confidently on top of it.
    """
    findings = [
        Finding("trace_is_intact", ERROR, problem) for problem in trace.parse_errors
    ]
    if not trace.events:
        findings.append(Finding("trace_is_intact", ERROR, "trace contains no events"))
        return findings

    sequences = [event.seq for event in trace.events]
    duplicates = sorted({seq for seq in sequences if sequences.count(seq) > 1})
    if duplicates:
        findings.append(
            Finding(
                "trace_is_intact", ERROR, f"duplicate sequence numbers: {duplicates}"
            )
        )
    expected = list(range(1, len(sequences) + 1))
    if sorted(set(sequences)) != expected[: len(set(sequences))] or sequences[0] != 1:
        findings.append(
            Finding(
                "trace_is_intact",
                ERROR,
                f"sequence is not contiguous from 1: {sequences}",
            )
        )
    return findings


def every_tool_call_has_a_result(trace: Trace, case) -> List[Finding]:
    """A call with no result is a tool that raised and was swallowed.

    The answer still comes back, often plausibly, built on one input fewer than it claims.
    This is the shape of failure that output evals are worst at: nothing looks wrong.
    """
    findings = []
    results = trace.named("tool.result")
    for call in trace.tool_calls():
        matching = [
            result
            for result in results
            if result.get("tool") == call.get("tool") and result.seq > call.seq
        ]
        if not matching:
            findings.append(
                Finding(
                    "every_tool_call_has_a_result",
                    ERROR,
                    f"{call.get('tool')!r} was called and never returned",
                    call.seq,
                )
            )
    return findings


def trace_reaches_a_terminal_event(trace: Trace, case) -> List[Finding]:
    terminal = ("request.completed", "write.proposed")
    if any(trace.named(name) for name in terminal):
        return []
    if not trace.events:
        # `trace_is_intact` already reports the empty trace. Saying it twice tells the
        # reader there are two problems when there is one.
        return []
    return [
        Finding(
            "trace_reaches_a_terminal_event",
            ERROR,
            f"trace ends on {trace.names()[-1]!r} with no terminal event; "
            "the run did not finish",
        )
    ]


ALL_CHECKS: tuple = (
    trace_is_intact,
    route_matches_expectation,
    fallback_was_not_used_as_a_guess,
    write_requires_prior_approval,
    approval_matches_the_proposal,
    pending_run_changed_nothing,
    every_tool_call_has_a_result,
    write_proposal_is_grounded,
    no_redundant_tool_calls,
    trace_reaches_a_terminal_event,
)


def run_checks(trace: Trace, case, checks=ALL_CHECKS) -> List[Finding]:
    findings: List[Finding] = []
    for check in checks:
        findings.extend(check(trace, case))
    return sorted(
        findings, key=lambda f: (SEVERITY_ORDER.index(f.severity), f.seq or 0)
    )


def _canonical(value) -> str:
    try:
        return json.dumps(value, sort_keys=True, default=str)
    except TypeError:
        return repr(value)


def _short(digest) -> str:
    return f"{str(digest)[:12]}…" if digest else "(none)"
