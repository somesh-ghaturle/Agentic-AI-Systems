"""Focused API tests for the human-in-the-loop dashboard."""

import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "dashboard_app", ROOT / "examples/hermes-dashboard/backend/app.py"
)
dashboard = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = dashboard
SPEC.loader.exec_module(dashboard)


class TestDashboardBoundary(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        dashboard._approvals.clear()

    async def test_fingerprint_is_recomputed_and_decision_is_single_use(self):
        request = dashboard.ApprovalRequest(
            tool="restart_service", arguments={"service": "billing"}, rationale="clear pool"
        )
        created = await dashboard.create_approval(request)
        self.assertEqual(created["status"], "pending")
        decided = await dashboard.decide(
            created["id"], dashboard.DecisionRequest(decision="approve", actor="alice")
        )
        self.assertEqual(decided["status"], "approve")
        with self.assertRaises(dashboard.HTTPException):
            await dashboard.decide(
                created["id"], dashboard.DecisionRequest(decision="reject", actor="bob")
            )

    async def test_tampered_fingerprint_is_rejected(self):
        request = dashboard.ApprovalRequest(
            tool="delete_record",
            arguments={"id": "incident-1"},
            rationale="requested",
            fingerprint="tampered",
        )
        with self.assertRaises(dashboard.HTTPException):
            await dashboard.create_approval(request)


if __name__ == "__main__":
    unittest.main()
