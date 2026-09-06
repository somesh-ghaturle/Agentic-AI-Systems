"""Tests for the second-path example.

The interesting group is the last one. `TestTheGateIsCorrect` is the suite someone writing
this system would write, and every assertion in it passes whether or not the boundary holds
overall -- which is the example's whole claim, asserted here rather than described.

    python3 -m unittest tests.test_second_path -v
"""

import importlib.util
import io
import pathlib
import sys
import unittest

# By path under a unique name -- see the note in test_budget_guard.py.
ROOT = pathlib.Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "second_path_example", ROOT / "examples/second-path" / "boundary.py"
)
bd = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = bd
SPEC.loader.exec_module(bd)

ARGS = {"service": "billing"}


class TestTheGateIsCorrect(unittest.TestCase):
    """The control everyone points at. Nothing here ever fails, including in the broken
    configuration -- that is the point, and TestTheGateIsNotEnough asserts it directly."""

    def setUp(self):
        bd.EFFECTS.clear()
        self.gate = bd.ApprovalGate()

    def test_write_with_no_claim_is_refused(self):
        # The message is asserted, not just the refusal. Without the `claim is None` branch the
        # call is still refused -- None != the digest -- so a test that only checked for Refused
        # would pass with the branch deleted, and the operator would be told their approval did
        # not match when in fact they never sent one. Attribution is the behaviour here.
        with self.assertRaises(bd.Refused) as caught:
            self.gate.execute("restart_service", ARGS, None)
        self.assertIn("no approval claim", str(caught.exception))
        self.assertEqual(bd.EFFECTS, [])

    def test_write_with_a_mismatched_claim_is_refused(self):
        claim = bd.fingerprint("restart_service", {"service": "payments"})
        with self.assertRaises(bd.Refused) as caught:
            self.gate.execute("restart_service", ARGS, claim)
        self.assertIn("does not match", str(caught.exception))
        self.assertEqual(bd.EFFECTS, [])

    def test_write_with_the_matching_claim_runs(self):
        claim = bd.fingerprint("restart_service", ARGS)
        self.gate.execute("restart_service", ARGS, claim)
        self.assertEqual(bd.EFFECTS, ["restarted billing"])

    def test_a_claim_is_bound_to_the_arguments_not_the_tool(self):
        # Approving a restart of 'payments' must not authorise a restart of 'billing'.
        self.assertNotEqual(
            bd.fingerprint("restart_service", {"service": "payments"}),
            bd.fingerprint("restart_service", ARGS),
        )

    def test_argument_order_does_not_change_the_claim(self):
        a = bd.fingerprint("restart_service", {"service": "billing", "reason": "oom"})
        b = bd.fingerprint("restart_service", {"reason": "oom", "service": "billing"})
        self.assertEqual(a, b)

    def test_reads_need_no_claim(self):
        self.assertIn("healthy", self.gate.execute("get_status", ARGS, None))


class TestTheDesignedBoundary(unittest.TestCase):
    """The orchestrator as intended: a read-only caller."""

    def setUp(self):
        bd.EFFECTS.clear()

    def test_the_write_tool_is_not_reachable(self):
        with self.assertRaises(bd.Refused):
            bd.Orchestrator().call("restart_service", ARGS)
        self.assertEqual(bd.EFFECTS, [])

    def test_reads_still_work(self):
        self.assertIn("healthy", bd.Orchestrator().call("get_status", ARGS))

    def test_no_writes_are_reachable(self):
        self.assertEqual(bd.reachable_writes(bd.Orchestrator()), [])


class TestTheSecondPath(unittest.TestCase):
    """The one-word edit. The gate is untouched and still correct."""

    def setUp(self):
        bd.EFFECTS.clear()
        self.wide = bd.Orchestrator(bd.TOOLS)

    def test_the_write_executes_with_no_approval(self):
        self.wide.call("restart_service", ARGS)
        self.assertEqual(bd.EFFECTS, ["restarted billing"])

    def test_the_gate_was_never_consulted(self):
        # There is no claim anywhere in this call, and the effect happened anyway. The gate did
        # not fail open; it was not on the path.
        self.wide.call("restart_service", ARGS)
        self.assertEqual(bd.EFFECTS, ["restarted billing"])

    def test_reachable_writes_names_it(self):
        self.assertEqual(bd.reachable_writes(self.wide), ["restart_service"])


class TestTheGateIsNotEnough(unittest.TestCase):
    """The example's central claim, asserted rather than described: the gate suite passes in
    the broken configuration, so a green gate suite is not evidence the boundary holds."""

    def test_every_gate_assertion_still_passes_in_the_broken_configuration(self):
        bd.Orchestrator(bd.TOOLS).call("restart_service", ARGS)  # the boundary is open

        result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(
            unittest.TestLoader().loadTestsFromTestCase(TestTheGateIsCorrect)
        )
        self.assertTrue(result.wasSuccessful())
        self.assertGreater(result.testsRun, 0)

    def test_the_reachability_check_is_what_separates_the_two(self):
        # Same gate, same tools, different reachable set -- and only this check can tell them
        # apart. If it ever returns [] for the wide orchestrator, the example is broken.
        self.assertEqual(bd.reachable_writes(bd.Orchestrator()), [])
        self.assertEqual(bd.reachable_writes(bd.Orchestrator(bd.TOOLS)), ["restart_service"])


class TestToolContract(unittest.TestCase):
    def test_an_unknown_access_level_is_refused_at_construction(self):
        with self.assertRaises(ValueError):
            bd.Tool("x", "admin", lambda a: "")

    def test_read_tools_holds_only_reads(self):
        self.assertTrue(all(t.access == "read" for t in bd.READ_TOOLS.values()))


if __name__ == "__main__":
    unittest.main()
