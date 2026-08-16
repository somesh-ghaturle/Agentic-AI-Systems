"""Smoke tests for the starter agent.

unittest rather than pytest: every other suite in this repository — both example suites and
all six under infra/ — is stdlib unittest, and pytest is in no requirements file here. As
bare pytest-style functions these tests were collected by nothing and had never run.

    python3 -m unittest tests.test_agent -v
"""

import pathlib
import subprocess
import sys
import unittest

AGENT = (
    pathlib.Path(__file__).resolve().parent.parent
    / "examples"
    / "starter-agent"
    / "agent.py"
)


def run_agent(args):
    """Run the agent as a subprocess, the way a user would.

    The path is derived from this file rather than the working directory, so the suite
    passes from anywhere instead of only from the repository root.
    """
    result = subprocess.run(
        [sys.executable, str(AGENT), *args], capture_output=True, text=True
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


class TestStarterAgent(unittest.TestCase):
    def test_agent_echoes_an_unmatched_prompt(self):
        code, out, err = run_agent(["hello"])
        self.assertEqual(code, 0, err)
        self.assertIn("Agent received", out)

    def test_agent_selects_the_search_action(self):
        code, out, err = run_agent(["please", "search", "for", "X"])
        self.assertEqual(code, 0, err)
        self.assertIn("Action: search", out)


if __name__ == "__main__":
    unittest.main()
