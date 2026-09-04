"""Focused API tests for the human-in-the-loop dashboard.

    python3 -m unittest tests.test_hermes_dashboard -v

The dashboard backend imports fastapi and pydantic, and this module executes it at import time
rather than importing it normally. Without a guard that execution raises inside the dependency-
free `examples` CI job and in any working tree that has not installed this example's pinned
requirements, which reports a missing package as a broken test module. Task 47 fixed the same
shape in tests/test_e2e_agent.py; the guard belongs wherever a suite reaches for a dependency
the fast job does not install.
"""

import importlib.util
import pathlib
import sys
import unittest


def _absent(name):
    # find_spec on a dotted name imports the parent to look inside it, so it raises rather
    # than returning None when the parent is absent. Either way the module is unavailable.
    try:
        return importlib.util.find_spec(name) is None
    except (ImportError, ValueError):
        return True


_MISSING = [m for m in ("fastapi", "pydantic") if _absent(m)]

ROOT = pathlib.Path(__file__).resolve().parent.parent
dashboard = None

if not _MISSING:
    SPEC = importlib.util.spec_from_file_location(
        "dashboard_app", ROOT / "examples/hermes-dashboard/backend/app.py"
    )
    dashboard = importlib.util.module_from_spec(SPEC)
    sys.modules[SPEC.name] = dashboard
    SPEC.loader.exec_module(dashboard)


@unittest.skipIf(
    _MISSING,
    f"hermes-dashboard dependencies are not installed ({', '.join(_MISSING)}); "
    "this suite runs in the example-deps job",
)
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
