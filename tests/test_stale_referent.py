"""Tests for the stale-referent example.

The interesting group is `TestTheGateIsNotEnough`. `TestTheGateIsCorrect` is the suite someone
writing this system would write, and every assertion in it passes while a $50 approval executes
a $5,000 refund -- which is the example's claim, asserted here rather than described.

    python3 -m unittest tests.test_stale_referent -v
"""

import importlib.util
import io
import pathlib
import sys
import unittest

# By path under a unique name -- see the note in test_budget_guard.py.
ROOT = pathlib.Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "stale_referent_example", ROOT / "examples/stale-referent" / "referent.py"
)
rf = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = rf
SPEC.loader.exec_module(rf)

ARGS = {"order": "A-42"}


def _reset():
    rf.LEDGER["A-42"] = {"amount_cents": 5_000, "customer": "c-1", "status": "open"}
    rf.EFFECTS.clear()


class TestTheGateIsCorrect(unittest.TestCase):
    """The control everyone points at. Nothing here fails, including while the ledger has moved
    underneath an approval -- which is what TestTheGateIsNotEnough asserts directly."""

    def setUp(self):
        _reset()
        self.gate = rf.ApprovalGate()

    def test_write_with_no_claim_is_refused(self):
        # The message is asserted, not only the refusal: without the `claim is None` branch the
        # call is still refused, and the operator is told their approval did not match when in
        # fact they never sent one.
        with self.assertRaises(rf.Refused) as caught:
            self.gate.execute("refund", ARGS, None)
        self.assertIn("no approval claim", str(caught.exception))
        self.assertEqual(rf.EFFECTS, [])

    def test_a_claim_for_another_order_is_refused(self):
        claim = rf.fingerprint("refund", {"order": "B-7"})
        with self.assertRaises(rf.Refused) as caught:
            self.gate.execute("refund", ARGS, claim)
        self.assertIn("does not match", str(caught.exception))
        self.assertEqual(rf.EFFECTS, [])

    def test_a_claim_for_another_tool_is_refused(self):
        claim = rf.fingerprint("restart_service", ARGS)
        with self.assertRaises(rf.Refused):
            self.gate.execute("refund", ARGS, claim)
        self.assertEqual(rf.EFFECTS, [])

    def test_the_matching_claim_runs(self):
        approval = self.gate.review("refund", ARGS)
        self.gate.execute("refund", ARGS, approval.claim)
        self.assertEqual(rf.EFFECTS, ["refunded 5000 to c-1"])


class TestTheGateIsNotEnough(unittest.TestCase):
    """The central claim, asserted: the gate suite is green while the wrong amount goes out."""

    def setUp(self):
        _reset()

    def test_the_approved_amount_and_the_executed_amount_differ(self):
        gate = rf.ApprovalGate()
        approval = gate.review("refund", ARGS)
        self.assertEqual(approval.shown["amount_cents"], 5_000)

        rf.LEDGER["A-42"]["amount_cents"] = 500_000
        gate.execute("refund", ARGS, approval.claim)  # allowed: same call, same claim

        self.assertEqual(rf.EFFECTS, ["refunded 500000 to c-1"])

    def test_every_gate_assertion_still_passes_while_that_is_true(self):
        gate = rf.ApprovalGate()
        approval = gate.review("refund", ARGS)
        rf.LEDGER["A-42"]["amount_cents"] = 500_000
        gate.execute("refund", ARGS, approval.claim)
        self.assertEqual(rf.EFFECTS, ["refunded 500000 to c-1"])

        result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(
            unittest.TestLoader().loadTestsFromTestCase(TestTheGateIsCorrect)
        )
        self.assertTrue(result.wasSuccessful())
        self.assertGreater(result.testsRun, 0)

    def test_the_fingerprint_is_identical_before_and_after(self):
        # Why the existing check cannot catch this: the arguments never moved.
        before = rf.fingerprint("refund", ARGS)
        rf.LEDGER["A-42"]["amount_cents"] = 500_000
        self.assertEqual(before, rf.fingerprint("refund", ARGS))


class TestDrift(unittest.TestCase):
    """The check that separates the two, and the refusal it produces."""

    def setUp(self):
        _reset()
        self.gate = rf.ApprovalGate()

    def test_no_drift_when_the_world_is_unchanged(self):
        self.assertEqual(rf.drift(self.gate.review("refund", ARGS)), {})

    def test_drift_names_the_field_and_both_values(self):
        approval = self.gate.review("refund", ARGS)
        rf.LEDGER["A-42"]["amount_cents"] = 500_000
        self.assertEqual(rf.drift(approval), {"amount_cents": (5_000, 500_000)})

    def test_drift_covers_every_fact_the_reviewer_saw(self):
        # Not just the amount. A refund reassigned to another customer is the same failure.
        approval = self.gate.review("refund", ARGS)
        rf.LEDGER["A-42"]["customer"] = "c-999"
        self.assertEqual(rf.drift(approval), {"customer": ("c-1", "c-999")})

    def test_bound_execution_refuses_and_says_what_moved(self):
        approval = self.gate.review("refund", ARGS)
        rf.LEDGER["A-42"]["amount_cents"] = 500_000
        with self.assertRaises(rf.Refused) as caught:
            rf.execute_bound(self.gate, approval)
        message = str(caught.exception)
        self.assertIn("binding:", message)
        self.assertIn("amount_cents: 5000 -> 500000", message)
        self.assertEqual(rf.EFFECTS, [])

    def test_bound_execution_runs_when_nothing_moved(self):
        approval = self.gate.review("refund", ARGS)
        rf.execute_bound(self.gate, approval)
        self.assertEqual(rf.EFFECTS, ["refunded 5000 to c-1"])

    def test_bound_execution_still_enforces_the_claim(self):
        # The binding is an addition to the gate, not a replacement for it.
        approval = rf.Approval(
            tool="refund", arguments=dict(ARGS), claim="not-a-digest", shown=rf.resolve(ARGS)
        )
        with self.assertRaises(rf.Refused) as caught:
            rf.execute_bound(self.gate, approval)
        self.assertIn("does not match", str(caught.exception))
        self.assertEqual(rf.EFFECTS, [])


if __name__ == "__main__":
    unittest.main()
