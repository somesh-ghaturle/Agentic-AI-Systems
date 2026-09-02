"""Locks in the overflow example's retention bug and the fix.

    python3 -m unittest tests.test_context_overflow -v

No dependencies; these run in the fast `examples` CI job.
"""

import pathlib
import sys
import unittest

sys.path.insert(
    0,
    str(pathlib.Path(__file__).resolve().parent.parent / "examples" / "context-overflow"),
)

import overflow as ov


class TestOverflowBehaviour(unittest.TestCase):
    def test_a_budgeted_window_can_exceed_the_limit(self):
        self.assertGreater(ov.total_tokens(ov.HISTORY), 80)

    def test_truncation_keeps_the_recent_tail(self):
        kept, _ = ov.truncate_by_recency(ov.HISTORY, 80)
        self.assertIn("test run: 46 passed", " ".join(content for _, content in kept))
        self.assertNotIn("DECISION: Single-table design", " ".join(content for _, content in kept))

    def test_critical_messages_survive_even_when_old(self):
        kept, _ = ov.keep_critical_messages(ov.HISTORY, 80)
        self.assertTrue(any("DECISION:" in content for _, content in kept))
        self.assertTrue(any("OPEN QUESTION:" in content for _, content in kept))
        self.assertTrue(any(role == "system" for role, _ in kept))

    def test_negative_budget_is_rejected(self):
        with self.assertRaises(ValueError):
            ov.truncate_by_recency(ov.HISTORY, -1)
        with self.assertRaises(ValueError):
            ov.keep_critical_messages(ov.HISTORY, -1)


if __name__ == "__main__":
    unittest.main()
