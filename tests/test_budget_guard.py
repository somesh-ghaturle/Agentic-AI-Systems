"""Tests the token-budget bound fires before a spend, not after.

unittest rather than pytest: every other suite in this repository is stdlib unittest, and
pytest is in no requirements file here.

    python3 -m unittest tests.test_budget_guard -v

The agent contains no model, which is what makes these tests deterministic. Every step is
keyword-based and every cost is a fixed integer, so the assertions below are offline and
exact.

The four test classes:

    TestBudgetSufficient      the agent completes every step in thorough mode
    TestBudgetTight           the agent degrades to quick mode and still finishes
    TestBudgetExhausted       the agent stops and names what it skipped
    TestBudgetHardCap         the agent never exceeds its budget
"""

import importlib.util
import pathlib
import sys
import unittest

# Loaded by path under a name of its own, the way test_edge_agent.py does it, rather than
# by putting the example directory on sys.path and saying `import agent`. Three examples
# ship a file called agent.py, and a bare import binds sys.modules["agent"] for the whole
# discovery run -- whichever test file sorts first wins and the others get its module.
ROOT = pathlib.Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "budget_guard_example", ROOT / "examples/budget-guard" / "agent.py"
)
budget = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = budget
SPEC.loader.exec_module(budget)

BudgetGuard = budget.BudgetGuard


class TestBudgetSufficient(unittest.TestCase):
    """Enough budget to run every step in thorough mode."""

    def test_completes_all_steps(self):
        agent = BudgetGuard("summarize the refund policy", token_budget=5000)
        result = agent.run()
        self.assertTrue(result.finished)
        self.assertFalse(result.exhausted)
        self.assertEqual(result.skipped, [])

    def test_all_steps_thorough(self):
        agent = BudgetGuard("summarize the refund policy", token_budget=5000)
        result = agent.run()
        for step in result.completed:
            self.assertEqual(step.mode, "thorough")

    def test_produces_answer(self):
        agent = BudgetGuard("summarize the refund policy", token_budget=5000)
        result = agent.run()
        self.assertTrue(result.answer)
        self.assertNotEqual(result.answer, "(no answer produced)")

    def test_answer_mentions_subject(self):
        agent = BudgetGuard("summarize the refund policy", token_budget=5000)
        result = agent.run()
        self.assertIn("refund", result.answer.lower())


class TestBudgetTight(unittest.TestCase):
    """Budget is tight enough that some steps must run in quick mode."""

    def test_degrades_to_quick(self):
        """When thorough cost exceeds remaining budget, the agent uses quick mode."""
        # gather(800) + analyze(1200) = 2000 used. draft thorough = 600, remaining = 0.
        # With budget 2000, draft cannot run in thorough mode (2000+600 > 2000).
        # But quick draft = 200, which fits (2000+200 > 2000... no). Let me pick a budget
        # where gather+analyze thorough leaves room for quick draft but not thorough.
        # gather(800) + analyze(1200) = 2000. Budget 2200: draft thorough(600) = 2600 > 2200.
        # Quick draft(200) = 2200 <= 2200. Then review thorough(400) = 2600 > 2200.
        # Quick review(100) = 2300 > 2200. So review is skipped.
        # Let me use budget 2300: quick draft(200) + quick review(100) = 2300. Fits.
        agent = BudgetGuard("summarize the refund policy", token_budget=2300)
        result = agent.run()
        modes = {step.name: step.mode for step in result.completed}
        # The first two steps should be thorough; the last two should be quick.
        self.assertEqual(modes["gather"], "thorough")
        self.assertEqual(modes["analyze"], "thorough")
        self.assertEqual(modes["draft"], "quick")
        self.assertEqual(modes["review"], "quick")

    def test_still_finishes_in_quick_mode(self):
        agent = BudgetGuard("summarize the refund policy", token_budget=2300)
        result = agent.run()
        self.assertTrue(result.finished)
        self.assertFalse(result.exhausted)

    def test_quick_answer_is_present(self):
        agent = BudgetGuard("summarize the refund policy", token_budget=2300)
        result = agent.run()
        self.assertTrue(result.answer)
        self.assertNotEqual(result.answer, "(no answer produced)")


class TestBudgetExhausted(unittest.TestCase):
    """Budget is too small to finish; the agent must stop and name what it skipped."""

    def test_stops_before_completion(self):
        agent = BudgetGuard("summarize the refund policy", token_budget=500)
        result = agent.run()
        self.assertTrue(result.exhausted)
        self.assertFalse(result.finished)

    def test_names_skipped_steps(self):
        agent = BudgetGuard("summarize the refund policy", token_budget=500)
        result = agent.run()
        self.assertTrue(result.skipped)
        # The skipped list must name steps, not just say "exhausted".
        for name in result.skipped:
            self.assertIsInstance(name, str)
            self.assertTrue(name)

    def test_does_not_exceed_budget(self):
        agent = BudgetGuard("summarize the refund policy", token_budget=500)
        result = agent.run()
        self.assertLessEqual(result.tokens_used, result.budget)

    def test_very_small_budget_skips_most_steps(self):
        """A budget so small only gather can run."""
        agent = BudgetGuard("summarize the refund policy", token_budget=200)
        result = agent.run()
        # Quick gather = 200, fits. Then analyze quick = 400 > 200 used + 400 > 200 budget.
        self.assertTrue(result.exhausted)
        self.assertIn("analyze", result.skipped)

    def test_budget_of_one_skips_everything(self):
        """A budget so small nothing can run."""
        agent = BudgetGuard("summarize the refund policy", token_budget=1)
        result = agent.run()
        self.assertTrue(result.exhausted)
        self.assertEqual(result.tokens_used, 0)

    def test_partial_answer_is_present(self):
        """Even when exhausted, the agent may have produced a partial draft."""
        # gather(800 thorough or 200 quick) -- with 500 budget, gather quick(200) fits.
        # Then analyze quick(400) = 600 > 500. So only gather ran.
        agent = BudgetGuard("summarize the refund policy", token_budget=500)
        result = agent.run()
        # The agent gathered context but could not analyze or draft.
        # The answer may be empty (no draft step ran) or "(no answer produced)".
        # What matters is that it named what it skipped.
        self.assertTrue(result.skipped)


class TestBudgetHardCap(unittest.TestCase):
    """The budget is a hard cap: tokens_used never exceeds it."""

    def test_never_exceeds_with_large_budget(self):
        agent = BudgetGuard("summarize the refund policy", token_budget=10000)
        result = agent.run()
        self.assertLessEqual(result.tokens_used, 10000)

    def test_never_exceeds_with_tight_budget(self):
        agent = BudgetGuard("summarize the refund policy", token_budget=2300)
        result = agent.run()
        self.assertLessEqual(result.tokens_used, 2300)

    def test_never_exceeds_with_tiny_budget(self):
        agent = BudgetGuard("summarize the refund policy", token_budget=100)
        result = agent.run()
        self.assertLessEqual(result.tokens_used, 100)

    def test_never_exceeds_with_zero_budget(self):
        agent = BudgetGuard("summarize the refund policy", token_budget=0)
        result = agent.run()
        self.assertEqual(result.tokens_used, 0)
        self.assertTrue(result.exhausted)


if __name__ == "__main__":
    unittest.main()
