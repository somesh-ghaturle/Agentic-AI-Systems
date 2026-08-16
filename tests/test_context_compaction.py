"""Locks in the compaction retention policy, and the bug that made it necessary.

    python3 -m unittest tests.test_context_compaction -v

The first version classified the system message as ordinary prose and folded it into the
summary line, producing a compacted history with no instructions in it — compaction defeating
the thing it exists to serve. Found by running the demo and reading the output.

No dependencies; these run in the fast `examples` CI job.
"""

import pathlib
import sys
import unittest

sys.path.insert(
    0,
    str(pathlib.Path(__file__).resolve().parent.parent / "examples" / "context-compaction"),
)

import compact as cc


class TestTheRegression(unittest.TestCase):
    """The system message survives compaction, whatever else does not."""

    def test_the_system_message_is_kept(self):
        out, _ = cc.compact(cc.HISTORY)
        self.assertIn("system", [role for role, _ in out])
        self.assertEqual(out[0][1], cc.HISTORY[0][1])

    def test_it_survives_even_with_no_recency_allowance(self):
        """keep_recent=0 removes the safety net, so only the policy is left holding it up."""
        out, _ = cc.compact(cc.HISTORY, keep_recent=0)
        self.assertEqual(out[0][1], cc.HISTORY[0][1])

    def test_a_system_message_is_kept_even_when_it_looks_like_noise(self):
        history = [("system", "Reading the manual ..."), ("user", "hi")]
        out, _ = cc.compact(history, keep_recent=0)
        self.assertIn(("system", "Reading the manual ..."), out)

    def test_classify_puts_system_first(self):
        self.assertEqual(cc.classify("system", "test run: 41 passed"), "keep")


class TestRetentionPolicy(unittest.TestCase):
    def test_decisions_are_kept_verbatim(self):
        out, _ = cc.compact(cc.HISTORY)
        kept = [content for _, content in out]
        self.assertTrue(any("DECISION: single-table design" in c for c in kept))

    def test_open_questions_are_kept(self):
        out, _ = cc.compact(cc.HISTORY)
        self.assertTrue(any("OPEN QUESTION" in c for _, c in out))

    def test_tool_results_are_dropped(self):
        out, _ = cc.compact(cc.HISTORY, keep_recent=0)
        self.assertNotIn("tool", [role for role, _ in out])

    def test_progress_chatter_is_dropped(self):
        self.assertEqual(cc.classify("assistant", "Reading schema.sql ..."), "drop")
        self.assertEqual(cc.classify("assistant", "Checking query patterns ..."), "drop")

    def test_exploratory_prose_is_summarized_not_kept(self):
        self.assertEqual(
            cc.classify("assistant", "The orders.status column is an enum."), "summarize"
        )

    def test_a_summary_line_reports_what_was_omitted(self):
        out, stats = cc.compact(cc.HISTORY)
        summaries = [c for _, c in out if c.startswith("[compacted:")]
        self.assertEqual(len(summaries), 1)
        self.assertIn(str(stats["summarized"]), summaries[0])


class TestItBeatsTruncation(unittest.TestCase):
    """The claim the example exists to make, asserted rather than narrated."""

    def test_compaction_keeps_the_decision_that_truncation_loses(self):
        out, _ = cc.compact(cc.HISTORY)
        compacted = " ".join(c for _, c in out)
        truncated = " ".join(c for _, c in cc.HISTORY[-6:])
        self.assertIn("single-table design", compacted)
        self.assertNotIn("single-table design", truncated)

    def test_compaction_actually_shrinks_the_history(self):
        before = cc.total_tokens(cc.HISTORY)
        out, _ = cc.compact(cc.HISTORY)
        self.assertLess(cc.total_tokens(out), before)


class TestEdges(unittest.TestCase):
    def test_recent_messages_are_kept_regardless_of_class(self):
        out, _ = cc.compact(cc.HISTORY, keep_recent=2)
        self.assertEqual(out[-2:], cc.HISTORY[-2:])

    def test_keep_recent_larger_than_history_keeps_everything(self):
        out, _ = cc.compact(cc.HISTORY, keep_recent=500)
        self.assertEqual(out, cc.HISTORY)

    def test_a_negative_allowance_is_refused(self):
        with self.assertRaises(ValueError):
            cc.compact(cc.HISTORY, keep_recent=-1)

    def test_an_empty_history_compacts_to_nothing(self):
        out, stats = cc.compact([], keep_recent=0)
        self.assertEqual(out, [])
        self.assertEqual(stats, {"kept": 0, "summarized": 0, "dropped": 0})


if __name__ == "__main__":
    unittest.main()
