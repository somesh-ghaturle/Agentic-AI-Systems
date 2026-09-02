"""Focused tests for the local edge-agent boundary."""

import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "edge_example", ROOT / "examples/edge-agent" / "agent.py"
)
edge = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = edge
SPEC.loader.exec_module(edge)


class TestEdgeAgent(unittest.TestCase):
    def test_sqlite_state_round_trip(self):
        agent = edge.EdgeAgent()
        try:
            proposal = agent.propose_write("mode", "safe")
            self.assertIsNone(agent.read("mode"))
            with self.assertRaises(ValueError):
                agent.apply(edge.Proposal(proposal.token, "unknown", {}, "", 0))
            self.assertEqual(agent.snapshot(), {})
        finally:
            agent.close()

    def test_file_approval_is_exact_and_single_use(self):
        path = ROOT / "tests" / ".edge-approval-test.json"
        try:
            agent = edge.EdgeAgent(approval_path=path)
            try:
                proposal = agent.propose_write("mode", "safe")
                self.assertEqual(agent.approve(proposal.token), {"mode": "safe"})
                with self.assertRaises(FileNotFoundError):
                    agent.approvals.approve(proposal.token)
            finally:
                agent.close()
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
