#!/usr/bin/env python3
"""Tests for checkpoint-agent example."""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

import sys


class TestCheckpointAgent(unittest.TestCase):
    """Test checkpointing functionality."""

    @classmethod
    def setUpClass(cls):
        """Save the examples directory path."""
        cls.examples_dir = Path(__file__).parent

    def setUp(self):
        """Create a temporary directory for isolated state."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.original_dir = os.getcwd()

        # Copy agent.py to test directory
        shutil.copy(self.examples_dir / "agent.py", self.test_dir / "agent.py")

        # Change to test directory so relative imports work
        os.chdir(self.test_dir)

    def tearDown(self):
        """Clean up test directory."""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _import_agent(self):
        """Import agent module from test directory."""
        # Remove cached module if any
        if "agent" in sys.modules:
            del sys.modules["agent"]
        # Add test dir to path and import
        sys.path.insert(0, str(self.test_dir))
        from agent import CheckpointAgent
        return CheckpointAgent

    def test_initial_state_is_empty(self):
        """Agent starts with empty state when no checkpoint exists."""
        CheckpointAgent = self._import_agent()

        # Remove any existing state file
        state_file = self.test_dir / "state.json"
        if state_file.exists():
            state_file.unlink()

        agent = CheckpointAgent()
        self.assertEqual(agent.resume(), [])
        self.assertEqual(agent.state["current_step"], 0)

    def test_run_saves_action(self):
        """Running an action saves it to state."""
        CheckpointAgent = self._import_agent()
        agent = CheckpointAgent()
        result = agent.run("test-action")

        self.assertEqual(result, "Executing: test-action")
        self.assertIn("test-action", agent.resume())
        self.assertEqual(agent.state["current_step"], 1)

        # Verify state file exists and is valid JSON
        state_file = self.test_dir / "state.json"
        self.assertTrue(state_file.exists())
        state = json.loads(state_file.read_text())
        self.assertIn("test-action", state["completed_actions"])

    def test_idempotency(self):
        """Running the same action twice only records it once."""
        CheckpointAgent = self._import_agent()
        agent = CheckpointAgent()

        result1 = agent.run("repeated-action")
        result2 = agent.run("repeated-action")

        self.assertEqual(result1, "Executing: repeated-action")
        self.assertEqual(result2, "Already completed: repeated-action")
        self.assertEqual(len(agent.resume()), 1)
        self.assertEqual(agent.state["current_step"], 1)  # Only incremented once

    def test_resume_after_restart(self):
        """Agent can resume state after being recreated."""
        CheckpointAgent = self._import_agent()

        # First agent run
        agent1 = CheckpointAgent()
        agent1.run("action1")
        agent1.run("action2")

        # Simulate restart by creating new agent
        agent2 = CheckpointAgent()

        self.assertEqual(agent2.resume(), ["action1", "action2"])
        self.assertEqual(agent2.state["current_step"], 2)

    def test_multiple_actions(self):
        """Multiple actions are recorded in order."""
        CheckpointAgent = self._import_agent()
        agent = CheckpointAgent()

        agent.run("first")
        agent.run("second")
        agent.run("third")

        self.assertEqual(agent.resume(), ["first", "second", "third"])
        self.assertEqual(agent.state["current_step"], 3)

    def test_state_file_format(self):
        """State file is formatted with indentation for readability."""
        CheckpointAgent = self._import_agent()
        agent = CheckpointAgent()
        agent.run("formatted-action")

        state_file = self.test_dir / "state.json"
        self.assertTrue(state_file.exists())
        content = state_file.read_text()

        # Verify it's pretty-printed (contains newlines from indent=2)
        self.assertIn("\n", content)
        # Verify it's valid JSON
        state = json.loads(content)
        self.assertIn("completed_actions", state)


if __name__ == "__main__":
    unittest.main()
