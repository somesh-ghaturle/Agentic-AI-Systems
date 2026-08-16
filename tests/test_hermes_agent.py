"""Tests for the Hermes router example.

Two kinds of test here, and the second kind is the point.

The behavioural tests check that requests route where they should and that an approved
write executes. Useful, ordinary.

The boundary tests check that a write *cannot* happen by the wrong path — that the router
holds no reference to a write callable, that a handler's toolbelt refuses one, that an
approval is bound to exact arguments, and that a token is spendable once. Those are the
properties the example claims, and a claim in a README that no test enforces is a claim
that decays into a comment describing what the code used to do.

Stdlib `unittest` so it runs with nothing installed, from the repo root:

    python3 -m unittest discover -s tests -v
"""

import os
import sys
import unittest

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples", "hermes-agent"),
)

from hermes import (
    READ,
    WRITE,
    ApprovalAlreadyUsed,
    ApprovalExecutor,
    ApprovalExpired,
    ApprovalMismatch,
    ApprovalStore,
    Hermes,
    Route,
    Router,
    Tool,
    Toolbelt,
    ToolRegistry,
    Tracer,
    UnknownApproval,
    UnknownTool,
    WriteBoundaryViolation,
    WriteProposal,
    fingerprint,
)
from hermes.demo import build_agent, build_registries


class FakeClock:
    """A clock the tests move by hand, so expiry is tested without sleeping."""

    def __init__(self, now=1000.0):
        self.now = now

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


class TestRouting(unittest.TestCase):
    def setUp(self):
        self.agent, self.executor = build_agent()

    def test_read_request_completes_without_approval(self):
        result = self.agent.handle("summarize incident-2291")
        self.assertEqual(result.intent, "research")
        self.assertFalse(result.pending)
        self.assertIn("connection pool exhaustion", result.output["answer"])

    def test_write_request_stops_at_a_proposal(self):
        result = self.agent.handle("restart the billing service")
        self.assertTrue(result.pending)
        self.assertIsNone(result.output)
        self.assertEqual(result.proposal.tool, "restart_service")
        self.assertEqual(result.proposal.arguments, {"service": "billing"})

    def test_keyword_matches_on_word_boundaries_not_substrings(self):
        # "th(is)" contains "is" and "(up)date" contains "up". A substring router sends
        # both of these to the status handler and logs a confident reason for it.
        self.assertEqual(self.agent.handle("summarize this incident").intent, "research")
        self.assertEqual(self.agent.handle("update the docs").intent, "unrouted")

    def test_write_intent_wins_over_read_intent_when_both_appear(self):
        # Route order is a policy decision: an ambiguous request goes to the path that
        # asks a human, not the one that answers on its own.
        result = self.agent.handle("find the stale records and delete incident-2291")
        self.assertEqual(result.intent, "act")
        self.assertTrue(result.pending)

    def test_unmatched_request_says_so_rather_than_guessing(self):
        result = self.agent.handle("banana")
        self.assertEqual(result.intent, "unrouted")
        self.assertIn("No route matched", result.output["answer"])

    def test_classification_reports_which_keyword_fired(self):
        route, keyword = self.agent.router.classify("please restart billing")
        self.assertEqual(route.intent, "act")
        self.assertEqual(keyword, "restart")

    def test_fallback_reports_no_keyword(self):
        route, keyword = self.agent.router.classify("banana")
        self.assertEqual(route.intent, "unrouted")
        self.assertIsNone(keyword)


# ---------------------------------------------------------------------------
# The write boundary
# ---------------------------------------------------------------------------


class TestWriteBoundary(unittest.TestCase):
    def setUp(self):
        self.agent, self.executor = build_agent()

    def test_router_holds_no_reference_to_any_write_tool(self):
        """The structural half of the boundary.

        Not "the router refuses to call write tools" — the router cannot name one. If a
        later refactor hands Hermes the full registry "so it can list capabilities", this
        fails, which is the moment to catch it.
        """
        _, write_registry = build_registries()
        for name in write_registry.names():
            self.assertFalse(
                self.agent.read_registry.has(name),
                f"write tool {name!r} is reachable from the router's registry",
            )
        self.assertEqual(self.agent.read_registry.access, READ)

    def test_toolbelt_refuses_a_write_tool_even_if_one_is_present(self):
        """The check half, tested against a registry deliberately corrupted past its guard.

        `ToolRegistry.register` would reject this, so the test writes straight into the
        private dict. That is the scenario worth covering: if the first lock is ever
        defeated, the second still has to hold.
        """
        read_registry = ToolRegistry(READ)
        smuggled = Tool("delete_everything", WRITE, "should never run", lambda args: "ran")
        read_registry._tools[smuggled.name] = smuggled

        belt = Toolbelt(read_registry)
        with self.assertRaises(WriteBoundaryViolation):
            belt.call("delete_everything", {})

    def test_write_tool_cannot_be_registered_as_read(self):
        read_registry = ToolRegistry(READ)
        with self.assertRaises(WriteBoundaryViolation):
            read_registry.register(Tool("restart", WRITE, "restart a thing", lambda a: None))

    def test_hermes_rejects_a_write_registry(self):
        _, write_registry = build_registries()
        with self.assertRaises(WriteBoundaryViolation):
            Hermes(Router((), Route("x", (), lambda r, t: None)), write_registry)

    def test_executor_rejects_a_read_registry(self):
        read_registry, _ = build_registries()
        with self.assertRaises(WriteBoundaryViolation):
            ApprovalExecutor(read_registry, ApprovalStore())

    def test_toolbelt_rejects_a_write_registry(self):
        _, write_registry = build_registries()
        with self.assertRaises(WriteBoundaryViolation):
            Toolbelt(write_registry)

    def test_executor_refuses_a_read_tool(self):
        """Keeps the two paths from collapsing into one with a check most calls skip."""
        mixed = ToolRegistry(WRITE)
        smuggled = Tool("kb_search", READ, "a read tool in the write registry", lambda a: "ran")
        mixed._tools[smuggled.name] = smuggled
        executor = ApprovalExecutor(mixed, ApprovalStore())

        proposal = WriteProposal.create("kb_search", {"query": "x"}, "should not run")
        approval = executor._approvals.grant("kb_search", {"query": "x"}, approver="someone")
        with self.assertRaises(WriteBoundaryViolation):
            executor.execute(proposal, approval.token)

    def test_unknown_tool_is_a_tool_error_not_a_boundary_violation(self):
        belt = Toolbelt(self.agent.read_registry)
        with self.assertRaises(UnknownTool):
            belt.call("no_such_tool", {})


# ---------------------------------------------------------------------------
# Approvals
# ---------------------------------------------------------------------------


class TestApprovals(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.store = ApprovalStore(clock=self.clock)
        self.agent, self.executor = build_agent(approvals=self.store)

    def _propose(self, request="restart the billing service"):
        return self.agent.handle(request).proposal

    def test_approved_write_executes(self):
        proposal = self._propose()
        approval = self.store.grant(proposal.tool, proposal.arguments, approver="alice")
        output = self.executor.execute(proposal, approval.token)
        self.assertEqual(output["restarted"], "billing")

    def test_approval_is_bound_to_the_exact_arguments(self):
        """Approving a restart of billing does not approve a restart of payments."""
        proposal = self._propose()
        approval = self.store.grant("restart_service", {"service": "payments"}, "alice")
        with self.assertRaises(ApprovalMismatch):
            self.executor.execute(proposal, approval.token)

    def test_approval_is_bound_to_the_exact_tool(self):
        proposal = self._propose()
        approval = self.store.grant("delete_record", proposal.arguments, "alice")
        with self.assertRaises(ApprovalMismatch):
            self.executor.execute(proposal, approval.token)

    def test_approval_is_single_use(self):
        proposal = self._propose()
        approval = self.store.grant(proposal.tool, proposal.arguments, approver="alice")
        self.executor.execute(proposal, approval.token)
        with self.assertRaises(ApprovalAlreadyUsed):
            self.executor.execute(proposal, approval.token)

    def test_approval_expires(self):
        proposal = self._propose()
        approval = self.store.grant(
            proposal.tool, proposal.arguments, approver="alice", ttl_seconds=60
        )
        self.clock.advance(61)
        with self.assertRaises(ApprovalExpired):
            self.executor.execute(proposal, approval.token)

    def test_unknown_token_is_rejected(self):
        proposal = self._propose()
        with self.assertRaises(UnknownApproval):
            self.executor.execute(proposal, "not-a-real-token")

    def test_failed_claim_does_not_run_the_tool(self):
        """A mismatch must fail before the side effect, not after it."""
        from hermes.demo import _SERVICE_STATE  # noqa: PLC0415

        before = _SERVICE_STATE["billing"]["restarts_today"]
        proposal = self._propose()
        approval = self.store.grant("restart_service", {"service": "payments"}, "alice")
        with self.assertRaises(ApprovalMismatch):
            self.executor.execute(proposal, approval.token)
        self.assertEqual(_SERVICE_STATE["billing"]["restarts_today"], before)

    def test_fingerprint_ignores_argument_ordering(self):
        """Otherwise an approval granted by one code path fails to match the same action
        arriving by another, intermittently, looking like a race."""
        self.assertEqual(
            fingerprint("t", {"a": 1, "b": 2}),
            fingerprint("t", {"b": 2, "a": 1}),
        )

    def test_fingerprint_distinguishes_values(self):
        self.assertNotEqual(
            fingerprint("t", {"service": "billing"}),
            fingerprint("t", {"service": "payments"}),
        )

    def test_proposal_fingerprint_matches_what_the_executor_checks(self):
        """The digest shown to a human is the digest the executor verifies."""
        proposal = self._propose()
        self.assertEqual(
            proposal.fingerprint, fingerprint(proposal.tool, proposal.arguments)
        )


# ---------------------------------------------------------------------------
# Tracing
# ---------------------------------------------------------------------------


class TestTracing(unittest.TestCase):
    def setUp(self):
        self.agent, self.executor = build_agent()

    def test_every_hop_shares_one_trace_id(self):
        tracer = Tracer()
        self.agent.handle("summarize incident-2291", tracer=tracer)
        self.assertTrue(tracer.events)
        self.assertEqual({event.trace_id for event in tracer.events}, {tracer.trace_id})

    def test_sequence_numbers_are_monotonic(self):
        tracer = Tracer()
        self.agent.handle("summarize incident-2291", tracer=tracer)
        sequences = [event.seq for event in tracer.events]
        self.assertEqual(sequences, sorted(sequences))
        self.assertEqual(sequences, list(range(1, len(sequences) + 1)))

    def test_read_path_traces_classification_and_tool_calls(self):
        tracer = Tracer()
        self.agent.handle("summarize incident-2291", tracer=tracer)
        names = tracer.event_names()
        self.assertEqual(names[0], "request.received")
        self.assertIn("request.classified", names)
        self.assertIn("tool.call", names)
        self.assertEqual(names[-1], "request.completed")

    def test_pending_write_is_traced_as_proposed_not_completed(self):
        tracer = Tracer()
        self.agent.handle("restart the billing service", tracer=tracer)
        names = tracer.event_names()
        self.assertIn("write.proposed", names)
        self.assertNotIn("request.completed", names)

    def test_execution_traces_the_claim_and_the_write(self):
        tracer = Tracer()
        result = self.agent.handle("restart the billing service", tracer=tracer)
        approval = self.agent.approvals.grant(
            result.proposal.tool, result.proposal.arguments, approver="alice"
        )
        self.executor.execute(result.proposal, approval.token, tracer=tracer)
        names = tracer.event_names()
        self.assertIn("approval.claimed", names)
        writes = [
            event
            for event in tracer.events
            if event.event == "tool.call" and event.attributes.get("access") == WRITE
        ]
        self.assertEqual(len(writes), 1)
        self.assertEqual(writes[0].attributes["tool"], "restart_service")
        # The claim is recorded before the call it authorises.
        self.assertLess(
            names.index("approval.claimed"), tracer.events[-1].seq
        )

    def test_events_serialise_to_one_json_object_per_line(self):
        import json  # noqa: PLC0415

        tracer = Tracer()
        self.agent.handle("summarize incident-2291", tracer=tracer)
        for event in tracer.events:
            parsed = json.loads(event.to_json())
            self.assertEqual(parsed["trace_id"], tracer.trace_id)
            self.assertIn("event", parsed)


if __name__ == "__main__":
    unittest.main()
