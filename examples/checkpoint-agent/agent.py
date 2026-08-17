#!/usr/bin/env python3
"""Checkpoint agent - demonstrates state persistence and crash recovery."""

import json
import sys
from pathlib import Path


class CheckpointAgent:
    """Agent that persists state between runs using JSON checkpoint files."""

    CHECKPOINT_FILE = Path(__file__).parent / "state.json"

    def __init__(self):
        """Load state from checkpoint file or initialize empty state."""
        self.state = self._load_state()

    def _load_state(self) -> dict:
        """Load state from checkpoint file. Returns empty state if file doesn't exist."""
        if self.CHECKPOINT_FILE.exists():
            try:
                return json.loads(self.CHECKPOINT_FILE.read_text())
            except (json.JSONDecodeError, IOError) as e:
                # Corrupted or unreadable state file - start fresh
                print(f"Warning: Could not load state: {e}. Starting with empty state.")
                return {"completed_actions": [], "current_step": 0}
        return {"completed_actions": [], "current_step": 0}

    def _save_state(self):
        """Save state to checkpoint file atomically."""
        # Write to temp file first, then rename for atomicity
        temp_file = self.CHECKPOINT_FILE.with_suffix(".tmp")
        try:
            temp_file.write_text(json.dumps(self.state, indent=2))
            temp_file.rename(self.CHECKPOINT_FILE)
        except IOError as e:
            print(f"Error saving state: {e}")
            # Clean up temp file if rename failed
            if temp_file.exists():
                temp_file.unlink()

    def run(self, action: str) -> str:
        """Execute an action and save checkpoint.

        Args:
            action: The action to execute

        Returns:
            Result string describing the execution
        """
        # Check if this action was already completed (idempotency)
        if action in self.state["completed_actions"]:
            return f"Already completed: {action}"

        # Simulate work
        result = f"Executing: {action}"
        self.state["completed_actions"].append(action)
        self.state["current_step"] += 1
        self._save_state()
        return result

    def resume(self) -> list:
        """Resume from last checkpoint.

        Returns:
            List of completed actions from previous runs
        """
        return self.state["completed_actions"]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 agent.py <action>")
        print("Example: python3 agent.py 'deploy-model'")
        sys.exit(1)

    agent = CheckpointAgent()
    action = sys.argv[1]
    result = agent.run(action)
    print(result)
    print(f"Completed actions: {agent.resume()}")
