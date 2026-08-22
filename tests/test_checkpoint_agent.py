"""Locks in the checkpoint agent's recovery contract, and the artifact that broke its demo.

    python3 -m unittest tests.test_checkpoint_agent -v

These tests used to live in examples/checkpoint-agent/test_checkpoint.py, where nothing ran
them. The examples CI job discovers tests/ and separately runs compileall over examples/, so a
suite parked inside the example directory was syntax-checked and never executed. Every other
example keeps its tests here, which is why this one now does too.

The checkpoint file is the entire subject of the example, so each test points CHECKPOINT_FILE at
a temporary directory rather than copying agent.py somewhere and chdir-ing to it. That matters
beyond tidiness: the example was once committed with a real state.json holding eight actions left
over from a run, and `agent.py action1` — the first command its own documentation gives you —
answered "Already completed: action1" and executed nothing. A test that writes into the
repository is one way a file like that gets created.

No dependencies; these run in the fast `examples` CI job.
"""

import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(
    0,
    str(pathlib.Path(__file__).resolve().parent.parent / "examples" / "checkpoint-agent"),
)

import agent as ca


class CheckpointTestCase(unittest.TestCase):
    """Redirects the checkpoint into a temp dir so no test can write into the repository."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        original = ca.CheckpointAgent.CHECKPOINT_FILE
        self.addCleanup(setattr, ca.CheckpointAgent, "CHECKPOINT_FILE", original)
        self.state_file = pathlib.Path(tmp.name) / "state.json"
        ca.CheckpointAgent.CHECKPOINT_FILE = self.state_file


class TestColdStart(CheckpointTestCase):
    """What a fresh clone sees."""

    def test_state_is_empty_when_no_checkpoint_exists(self):
        agent = ca.CheckpointAgent()
        self.assertEqual(agent.resume(), [])
        self.assertEqual(agent.state["current_step"], 0)

    def test_first_action_executes_rather_than_reporting_completion(self):
        # The regression that motivated gitignoring state.json: with a checkpoint committed,
        # this returned "Already completed" on a machine that had never run the example.
        self.assertEqual(ca.CheckpointAgent().run("action1"), "Executing: action1")


class TestCheckpointing(CheckpointTestCase):
    """Running an action records it durably."""

    def test_run_writes_the_action_to_the_state_file(self):
        agent = ca.CheckpointAgent()
        self.assertEqual(agent.run("test-action"), "Executing: test-action")
        self.assertIn("test-action", agent.resume())
        self.assertEqual(agent.state["current_step"], 1)

        self.assertTrue(self.state_file.exists())
        self.assertIn("test-action", json.loads(self.state_file.read_text())["completed_actions"])

    def test_actions_are_recorded_in_order(self):
        agent = ca.CheckpointAgent()
        for action in ("first", "second", "third"):
            agent.run(action)
        self.assertEqual(agent.resume(), ["first", "second", "third"])
        self.assertEqual(agent.state["current_step"], 3)

    def test_state_file_is_readable_json(self):
        ca.CheckpointAgent().run("formatted-action")
        content = self.state_file.read_text()
        self.assertIn("\n", content)  # indent=2, so a human can read a checkpoint
        self.assertIn("completed_actions", json.loads(content))


class TestRecovery(CheckpointTestCase):
    """The point of the example: surviving a restart without redoing work."""

    def test_a_new_agent_resumes_from_the_checkpoint(self):
        first = ca.CheckpointAgent()
        first.run("action1")
        first.run("action2")

        restarted = ca.CheckpointAgent()
        self.assertEqual(restarted.resume(), ["action1", "action2"])
        self.assertEqual(restarted.state["current_step"], 2)

    def test_replaying_an_action_does_not_repeat_the_work(self):
        agent = ca.CheckpointAgent()
        self.assertEqual(agent.run("repeated-action"), "Executing: repeated-action")
        self.assertEqual(agent.run("repeated-action"), "Already completed: repeated-action")
        self.assertEqual(len(agent.resume()), 1)
        self.assertEqual(agent.state["current_step"], 1)


if __name__ == "__main__":
    unittest.main()
