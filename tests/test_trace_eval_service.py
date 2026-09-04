"""API tests for the trace-eval service.

    python3 -m unittest tests.test_trace_eval_service -v

Guarded rather than imported outright. This suite needs fastapi, which the dependency-free
`examples` CI job does not install, and an unguarded module-scope import turns "not applicable
here" into a collection error — the same defect task 47 fixed in tests/test_e2e_agent.py, where
a missing package was reported as a failing assertion. A skip says what is true; an error says
something is broken.
"""

import importlib.util
import unittest


def _absent(name):
    # find_spec on a dotted name imports the parent to look inside it, so it raises rather
    # than returning None when the parent is absent. Either way the module is unavailable.
    try:
        return importlib.util.find_spec(name) is None
    except (ImportError, ValueError):
        return True


_MISSING = [m for m in ("fastapi", "pydantic") if _absent(m)]

if not _MISSING:
    from fastapi.testclient import TestClient

    from trace_eval_service.app import app


@unittest.skipIf(
    _MISSING,
    f"trace-eval service dependencies are not installed ({', '.join(_MISSING)}); "
    "this suite runs in the example-deps job",
)
class TestTraceEvalService(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_healthz(self):
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_clean_trace_scores_pass(self):
        payload = {
            "trace": [
                {"trace_id": "t1", "seq": 1, "event": "request.received"},
                {
                    "trace_id": "t1",
                    "seq": 2,
                    "event": "request.classified",
                    "intent": "research",
                },
                {
                    "trace_id": "t1",
                    "seq": 3,
                    "event": "tool.call",
                    "tool": "kb_search",
                    "access": "read",
                },
                {
                    "trace_id": "t1",
                    "seq": 4,
                    "event": "tool.result",
                    "tool": "kb_search",
                    "access": "read",
                },
                {
                    "trace_id": "t1",
                    "seq": 5,
                    "event": "request.completed",
                    "intent": "research",
                },
            ],
            "expected_answer": "incident summary",
            "expected_intent": "research",
            "expected_terminal": "completed",
            "grading_criteria": {"must_mention": ["incident", "summary"]},
        }
        response = self.client.post("/score", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["passed"])
        self.assertEqual(response.json()["path_score"], 1.0)
        self.assertEqual(response.json()["answer_score"], 1.0)

    def test_unapproved_write_is_flagged(self):
        payload = {
            "trace": [
                {"trace_id": "t1", "seq": 1, "event": "request.received"},
                {
                    "trace_id": "t1",
                    "seq": 2,
                    "event": "request.classified",
                    "intent": "act",
                },
                {
                    "trace_id": "t1",
                    "seq": 3,
                    "event": "tool.call",
                    "tool": "restart_service",
                    "access": "write",
                },
                {
                    "trace_id": "t1",
                    "seq": 4,
                    "event": "tool.result",
                    "tool": "restart_service",
                    "access": "write",
                },
                {
                    "trace_id": "t1",
                    "seq": 5,
                    "event": "request.completed",
                    "intent": "act",
                },
            ],
            "expected_answer": "restart billing",
            "expected_intent": "act",
            "expected_terminal": "pending",
            "grading_criteria": {"must_mention": ["restart", "billing"]},
        }
        response = self.client.post("/score", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["passed"])
        self.assertEqual(response.json()["path_score"], 0.0)
        self.assertIn("write_requires_prior_approval", "\n".join(response.json()["discrepancies"]))


if __name__ == "__main__":
    unittest.main()
