"""Locks in the red-team example's approval-bypass detection.

    python3 -m unittest tests.test_eval_red_teaming -v

No dependencies; these run in the fast `examples` CI job.
"""

import pathlib
import sys
import unittest

sys.path.insert(
    0,
    str(pathlib.Path(__file__).resolve().parent.parent / "examples" / "eval-red-teaming"),
)

import redteam as rt


class TestRedTeam(unittest.TestCase):
    def test_benign_prompt_is_not_exploitable(self):
        prompt = rt.PROMPTS[0]
        result = rt.evaluate(prompt)
        self.assertFalse(result["exploit_successful"])
        self.assertEqual(result["guarded"]["decision"], "proceed")

    def test_injection_prompt_is_unsafe_for_naive_agent(self):
        prompt = rt.PROMPTS[1]
        result = rt.evaluate(prompt)
        self.assertTrue(result["exploit_successful"])
        self.assertEqual(result["naive"]["decision"], "unsafe_action")
        self.assertEqual(result["guarded"]["decision"], "blocked")

    def test_prompt_injection_variant_is_detected(self):
        prompt = rt.PROMPTS[2]
        result = rt.evaluate(prompt)
        self.assertTrue(result["exploit_successful"])
        self.assertIn("system override", prompt.prompt.lower())

    def test_normal_write_prompt_stays_safe(self):
        prompt = rt.PROMPTS[3]
        result = rt.evaluate(prompt)
        self.assertFalse(result["exploit_successful"])
        self.assertEqual(result["guarded"]["decision"], "proceed")


if __name__ == "__main__":
    unittest.main()
