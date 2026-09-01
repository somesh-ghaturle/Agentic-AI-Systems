"""Locks in the approval-gate fuzzing suite.

    python3 -m unittest tests.test_approval_gate_fuzzing -v

No dependencies; these run in the fast `examples` CI job.
"""

import pathlib
import sys
import unittest

sys.path.insert(
    0,
    str(pathlib.Path(__file__).resolve().parent.parent / "examples" / "approval-gate-fuzzing"),
)

import fuzz as af


class TestApprovalGateFuzzing(unittest.TestCase):
    def test_benign_prompt_is_not_flagged(self):
        self.assertFalse(af.is_unsafe(af.PROMPTS[0].prompt))
        self.assertEqual(af.naive_model(af.PROMPTS[0].prompt)["decision"], "safe_read")
        self.assertEqual(af.guarded_model(af.PROMPTS[0].prompt)["decision"], "proceed")

    def test_override_phrase_is_detected(self):
        prompt = af.PROMPTS[1].prompt
        self.assertTrue(af.is_unsafe(prompt))
        self.assertEqual(af.naive_model(prompt)["decision"], "unsafe_action")
        self.assertEqual(af.guarded_model(prompt)["decision"], "blocked")

    def test_system_override_variation_is_detected(self):
        prompt = af.PROMPTS[2].prompt
        self.assertTrue(af.is_unsafe(prompt))
        self.assertEqual(af.guarded_model(prompt)["decision"], "blocked")

    def test_suite_catches_all_unsafe_variants(self):
        unsafe = [case for case in af.PROMPTS if case.expected_unsafe]
        self.assertEqual(len(unsafe), 3)
        results = af.run_suite()
        self.assertEqual(sum(1 for result in results if result["unsafe"]), 3)
        self.assertEqual(sum(1 for result in results if result["guarded"] == "blocked"), 3)


if __name__ == "__main__":
    unittest.main()
