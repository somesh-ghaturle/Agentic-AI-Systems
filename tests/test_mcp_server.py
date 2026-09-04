"""The write boundary holds when the tool list comes from a server.

    python3 -m unittest tests.test_mcp_server -v

examples/tool-discovery/ asked what stays true when tools are loaded from a directory instead of
declared in a module. This asks the next question: what stays true when they are advertised by a
server a client does not own. The interesting property is that discovery and authorization come
apart — a client can see `refund_order`, read its schema, and call it, and none of that is
permission to run it.

The tests are grouped by what they defend. TestDiscoveryIsNotAuthorization covers the gap
itself. TestTheGateHolds covers the claim rules. TestTheSplitIsStructural covers the reason the
gate cannot simply be forgotten — there is no collection of "all tools" for a call to resolve
against, so the branch that runs a tool without a claim can only see read tools.

No dependencies; runs in the fast `examples` CI job.
"""

import importlib.util
import json
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SERVER_PATH = ROOT / "examples/mcp-server/server.py"

_spec = importlib.util.spec_from_file_location("mcp_server_example", SERVER_PATH)
mcp = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = mcp
_spec.loader.exec_module(mcp)

REFUND_ARGS = {"order_id": "991", "amount": 4000.0}


def call(server, name, arguments):
    return server.handle(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        }
    )


class TestDiscoveryIsNotAuthorization(unittest.TestCase):
    def setUp(self):
        self.server = mcp.build_server()

    def test_the_write_tool_is_advertised_not_hidden(self):
        """Hiding it would be security by the client not guessing a name, which is not a gate."""
        listed = self.server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        names = [t["name"] for t in listed["result"]["tools"]]
        self.assertIn("refund_order", names)
        self.assertIn("look_up_order", names)

    def test_the_listing_says_which_tools_need_approval(self):
        listed = self.server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        annotations = {t["name"]: t["annotations"] for t in listed["result"]["tools"]}
        self.assertTrue(annotations["refund_order"]["requiresApproval"])
        self.assertFalse(annotations["refund_order"]["readOnlyHint"])
        self.assertFalse(annotations["look_up_order"]["requiresApproval"])

    def test_seeing_the_tool_does_not_let_you_run_it(self):
        response = call(self.server, "refund_order", REFUND_ARGS)
        self.assertEqual(response["error"]["code"], mcp.ApprovalRequired.code)

    def test_a_read_tool_needs_no_approval(self):
        response = call(self.server, "look_up_order", {"order_id": "991"})
        self.assertNotIn("error", response)
        self.assertIn("acme", response["result"]["content"][0]["text"])


class TestTheGateHolds(unittest.TestCase):
    def setUp(self):
        self.server = mcp.build_server()

    def _granted(self, arguments=None):
        return self.server.approvals.grant("refund_order", arguments or REFUND_ARGS).token

    def test_a_matching_approval_runs_the_tool(self):
        args = dict(REFUND_ARGS, approval_token=self._granted())
        response = call(self.server, "refund_order", args)
        self.assertNotIn("error", response)
        self.assertIn("refunded 4000.0", response["result"]["content"][0]["text"])

    def test_an_approval_for_different_arguments_is_refused(self):
        """The failure this defends against is approving $10 and executing $4,000."""
        small = {"order_id": "991", "amount": 10.0}
        token = self.server.approvals.grant("refund_order", small).token
        args = dict(REFUND_ARGS, approval_token=token)
        response = call(self.server, "refund_order", args)
        self.assertEqual(response["error"]["code"], mcp.ApprovalInvalid.code)

    def test_an_approval_is_single_use(self):
        token = self._granted()
        first = call(self.server, "refund_order", dict(REFUND_ARGS, approval_token=token))
        self.assertNotIn("error", first)
        second = call(self.server, "refund_order", dict(REFUND_ARGS, approval_token=token))
        self.assertEqual(second["error"]["code"], mcp.ApprovalInvalid.code)

    def test_an_unknown_token_is_refused(self):
        args = dict(REFUND_ARGS, approval_token="not-a-real-token")
        response = call(self.server, "refund_order", args)
        self.assertEqual(response["error"]["code"], mcp.ApprovalInvalid.code)

    def test_an_expired_approval_is_refused(self):
        now = [1000.0]
        server = mcp.build_server(mcp.ApprovalStore(clock=lambda: now[0]))
        token = server.approvals.grant("refund_order", REFUND_ARGS).token
        now[0] += mcp.APPROVAL_TTL_SECONDS + 1
        response = call(server, "refund_order", dict(REFUND_ARGS, approval_token=token))
        self.assertEqual(response["error"]["code"], mcp.ApprovalInvalid.code)

    def test_the_token_is_not_fingerprinted_as_an_argument(self):
        """Otherwise granting and claiming could never agree, since the grant has no token."""
        args = dict(REFUND_ARGS, approval_token=self._granted())
        self.assertNotIn("error", call(self.server, "refund_order", args))

    def test_the_audit_records_whether_the_call_was_approved(self):
        call(self.server, "look_up_order", {"order_id": "991"})
        call(self.server, "refund_order", dict(REFUND_ARGS, approval_token=self._granted()))
        self.assertEqual(
            self.server.audit,
            [
                {"tool": "look_up_order", "approved": False},
                {"tool": "refund_order", "approved": True},
            ],
        )


class TestTheSplitIsStructural(unittest.TestCase):
    def test_a_read_registry_refuses_a_write_tool(self):
        registry = mcp.ToolRegistry(mcp.READ)
        tool = mcp.Tool("x", mcp.WRITE, "d", {}, lambda: None)
        with self.assertRaises(mcp.WriteBoundaryViolation):
            registry.register(tool)

    def test_a_write_registry_refuses_a_read_tool(self):
        registry = mcp.ToolRegistry(mcp.WRITE)
        tool = mcp.Tool("x", mcp.READ, "d", {}, lambda: None)
        with self.assertRaises(mcp.WriteBoundaryViolation):
            registry.register(tool)

    def test_a_tool_cannot_declare_a_third_access_level(self):
        with self.assertRaises(mcp.WriteBoundaryViolation):
            mcp.Tool("x", "admin", "d", {}, lambda: None)

    def test_the_read_registry_never_holds_the_write_tool(self):
        """The reason the gate cannot be forgotten: the read path has nothing to forget it for."""
        server = mcp.build_server()
        self.assertFalse(server.read_tools.has("refund_order"))
        self.assertTrue(server.write_tools.has("refund_order"))

    def test_an_unknown_tool_is_an_error_not_a_silent_pass(self):
        response = call(mcp.build_server(), "drop_database", {})
        self.assertEqual(response["error"]["code"], mcp.UnknownTool.code)


class TestOverStdio(unittest.TestCase):
    """The server is a subprocess in real use, so at least one test treats it as one."""

    def _speak(self, *requests):
        payload = "\n".join(json.dumps(r) for r in requests)
        result = subprocess.run(
            [sys.executable, str(SERVER_PATH)],
            input=payload,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]

    def test_initialize_and_list_over_stdio(self):
        responses = self._speak(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        )
        self.assertEqual(responses[0]["result"]["serverInfo"]["name"], "approval-gated-example")
        self.assertIn("refund_order", [t["name"] for t in responses[1]["result"]["tools"]])

    def test_an_unapproved_write_is_refused_over_stdio(self):
        responses = self._speak(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "refund_order", "arguments": REFUND_ARGS},
            }
        )
        self.assertEqual(responses[0]["error"]["code"], mcp.ApprovalRequired.code)

    def test_malformed_input_is_a_parse_error_not_a_crash(self):
        result = subprocess.run(
            [sys.executable, str(SERVER_PATH)],
            input="{not json",
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["error"]["code"], -32700)


if __name__ == "__main__":
    unittest.main()
