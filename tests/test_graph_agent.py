"""Locks in graph-agent's routing, and the regression that made it necessary.

    python3 -m unittest tests.test_graph_agent -v

The classifier once held a bare keyword list and matched substrings, so "what is the refund
policy" — a question — routed to the **write** branch and drafted a refund for an order the
user had never mentioned. It was found by running the demo by hand. Nothing prevented it
coming back, because this example had no tests: importing it without langgraph installed used
to call sys.exit(), which a test runner cannot survive.

Both halves are fixed, and this file is the second half. The routing tests below need no
framework and run in the fast `examples` CI job; only the graph-topology tests need langgraph
and they skip without it.

A read/write classifier that fails *open* — toward the privileged branch — is the failure that
matters here, so most of these assert the read direction.
"""

import importlib.util
import pathlib
import sys
import unittest

sys.path.insert(
    0, str(pathlib.Path(__file__).resolve().parent.parent / "examples" / "graph-agent")
)

import graph_agent as ga

HAS_LANGGRAPH = importlib.util.find_spec("langgraph") is not None

# Imported here rather than inside the tests that use them, so ruff's top-level-import rule
# holds. They cannot be unconditional: the routing tests must still run with langgraph absent,
# which is the whole reason this file can exist at all — see the docstring.
if HAS_LANGGRAPH:
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.types import Command


def kind(request):
    return ga.classify({"request": request})["kind"]


class TestTheRegression(unittest.TestCase):
    """The exact strings that were misrouted, plus the family they belong to."""

    def test_the_original_bug_stays_fixed(self):
        self.assertEqual(kind("what is the refund policy"), "read")

    def test_questions_containing_write_nouns_are_reads(self):
        for request in [
            "what is the refund policy",
            "how do I cancel an order",
            "is a refund possible for order 4471",
            "does a refund take long",
            "can I cancel order 4471",
            "when will the charge appear",
            "why was I charged twice",
        ]:
            with self.subTest(request=request):
                self.assertEqual(kind(request), "read")

    def test_a_trailing_question_mark_is_enough(self):
        self.assertEqual(kind("refund policy?"), "read")

    def test_case_and_whitespace_do_not_change_the_verdict(self):
        self.assertEqual(kind("  WHAT IS THE REFUND POLICY  "), "read")


class TestWritesStillRoute(unittest.TestCase):
    """The fix must not have closed the branch entirely."""

    def test_imperative_actions_are_writes(self):
        for request in [
            "issue a refund for order 4471",
            "issue refund for order 4471",
            "cancel order 4471",
            "delete the customer record",
            "charge the card on file",
        ]:
            with self.subTest(request=request):
                self.assertEqual(kind(request), "write")


class TestFailsClosed(unittest.TestCase):
    """An unrecognised request must reach the read branch, not the write branch."""

    def test_an_unmatched_request_is_a_read(self):
        self.assertEqual(kind("hello there"), "read")

    def test_an_empty_request_is_a_read(self):
        self.assertEqual(kind(""), "read")

    def test_the_read_branch_is_the_harmless_one(self):
        """Documents *why* read is the safe default: it cannot propose an action."""
        state = ga.retrieve({"request": "hello there"})
        self.assertEqual(state["findings"], ["No matching knowledge."])


class TestReadPath(unittest.TestCase):
    def test_retrieval_finds_a_known_answer(self):
        state = ga.retrieve({"request": "what is the refund policy"})
        self.assertIn("30 days", state["findings"][0])

    def test_respond_uses_findings_when_no_answer_is_set(self):
        state = ga.respond({"findings": ["a", "b"]})
        self.assertEqual(state["answer"], "a b")

    def test_respond_leaves_an_existing_answer_alone(self):
        self.assertEqual(ga.respond({"answer": "done", "findings": ["x"]}), {})


class TestWritePathNeverActsUnapproved(unittest.TestCase):
    """The boundary itself, testable without the graph."""

    def test_draft_produces_a_proposal_not_an_effect(self):
        state = ga.draft({"request": "issue a refund for order 4471"})
        self.assertEqual(state["proposal"]["action"], "issue_refund")

    def test_execute_refuses_without_approval(self):
        state = ga.execute({"approved": False, "proposal": {"action": "issue_refund"}})
        self.assertIn("Refused", state["answer"])

    def test_execute_refuses_when_approval_is_absent_entirely(self):
        """Missing must behave as refused, not as permitted."""
        state = ga.execute({"proposal": {"action": "issue_refund"}})
        self.assertIn("Refused", state["answer"])

    def test_route_sends_writes_through_draft(self):
        self.assertEqual(ga.route({"kind": "write"}), "draft")
        self.assertEqual(ga.route({"kind": "read"}), "retrieve")


@unittest.skipUnless(HAS_LANGGRAPH, "langgraph not installed; runs in the example-deps job")
class TestDurableInterrupt(unittest.TestCase):
    """The property a production approval gate actually depends on.

    The example's claim is that an approval taking a day is the same code as one taking a
    second. That is only true if the suspended state lives in the checkpointer rather than in
    the graph object — otherwise "resume tomorrow" means "keep this Python process alive
    overnight", which is not the same claim at all.

    These tests use two separately-built graphs sharing one checkpointer. That is the closest
    honest proxy for a process restart that needs no database: if the second graph can resume
    what the first one suspended, the state is genuinely in the checkpointer.
    """

    def setUp(self):
        self.saver = InMemorySaver()

    def _config(self, thread_id):
        return {"configurable": {"thread_id": thread_id}}

    def test_a_caller_supplied_checkpointer_is_the_one_used(self):
        """Otherwise the argument is accepted and quietly ignored — the worst outcome."""
        graph = ga.build(checkpointer=self.saver)
        config = self._config("t-used")
        graph.invoke({"request": "issue a refund for order 4471"}, config)

        self.assertIsNotNone(
            self.saver.get(config),
            "nothing was written to the supplied checkpointer; build() ignored it",
        )

    def test_a_second_graph_resumes_what_the_first_suspended(self):
        """The state is in the checkpointer, not in the graph object."""
        config = self._config("t-handoff")

        suspended = ga.build(checkpointer=self.saver).invoke(
            {"request": "issue a refund for order 4471"}, config
        )
        self.assertIn("__interrupt__", suspended, "expected the write branch to suspend")

        # A different compiled graph, as a different process would build.
        resumed = ga.build(checkpointer=self.saver).invoke(Command(resume=True), config)

        self.assertNotIn("__interrupt__", resumed)
        self.assertIn("Executed", resumed["answer"])

    def test_a_refusal_survives_the_handoff_too(self):
        """The dangerous direction: a refusal must not become an approval across a restart."""
        config = self._config("t-refuse")
        ga.build(checkpointer=self.saver).invoke(
            {"request": "issue a refund for order 4471"}, config
        )
        resumed = ga.build(checkpointer=self.saver).invoke(Command(resume=False), config)

        self.assertIn("Refused", resumed["answer"])
        self.assertNotIn("Executed", resumed["answer"])

    def test_separate_checkpointers_do_not_share_threads(self):
        """A thread id is only meaningful within its checkpointer.

        Guards the reading of the seam that would be wrong in production: thread ids are not
        globally unique handles, so two deployments pointed at different stores cannot resume
        each other's approvals even with the same id.
        """
        config = self._config("t-isolated")
        ga.build(checkpointer=self.saver).invoke(
            {"request": "issue a refund for order 4471"}, config
        )

        other = InMemorySaver()
        self.assertIsNone(other.get(config))

    def test_default_checkpointer_still_works(self):
        """Passing nothing keeps the demo and the rest of the suite working."""
        graph = ga.build()
        result = graph.invoke(
            {"request": "what is the refund policy"}, self._config("t-default")
        )
        self.assertNotIn("__interrupt__", result)


@unittest.skipUnless(HAS_LANGGRAPH, "langgraph not installed; runs in the example-deps job")
class TestTopology(unittest.TestCase):
    """The declared graph, asserted as a value — which is the point of using one."""

    def test_approval_sits_between_draft_and_execute(self):
        graph = ga.build().get_graph()
        edges = {(e.source, e.target) for e in graph.edges}
        self.assertIn(("draft", "approval"), edges)
        self.assertIn(("approval", "execute"), edges)

    def test_there_is_no_edge_from_draft_straight_to_execute(self):
        """The gate cannot be bypassed by a topology change that still validates."""
        graph = ga.build().get_graph()
        edges = {(e.source, e.target) for e in graph.edges}
        self.assertNotIn(("draft", "execute"), edges)

    def test_the_read_branch_never_reaches_execute(self):
        graph = ga.build().get_graph()
        edges = {(e.source, e.target) for e in graph.edges}
        self.assertNotIn(("retrieve", "execute"), edges)
        self.assertIn(("retrieve", "respond"), edges)

    def test_a_read_request_returns_without_suspending(self):
        graph = ga.build()
        answer = ga.run(graph, "what is the refund policy", "t-read")
        self.assertIn("30 days", answer)

    def test_a_write_request_suspends_and_honours_a_refusal(self):
        graph = ga.build()
        answer = ga.run(graph, "issue a refund for order 4471", "t-no", approve=False)
        self.assertIn("Refused", answer)

    def test_a_write_request_executes_once_approved(self):
        graph = ga.build()
        answer = ga.run(graph, "issue a refund for order 4471", "t-yes", approve=True)
        self.assertIn("Executed", answer)


class TestImportSafety(unittest.TestCase):
    """The module must be importable without its dependency.

    This is what the rest of the file depends on, so it is asserted rather than assumed.
    """

    def test_importing_did_not_exit(self):
        self.assertTrue(hasattr(ga, "classify"))

    @unittest.skipIf(HAS_LANGGRAPH, "only meaningful when langgraph is absent")
    def test_build_raises_a_helpful_error_rather_than_exiting(self):
        with self.assertRaises(ImportError) as ctx:
            ga.build()
        self.assertIn("pip install", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
