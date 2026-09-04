#!/usr/bin/env python3
"""An MCP-shaped tool server whose writes cannot execute without an approval claim.

    python3 examples/mcp-server/server.py --demo
    echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python3 examples/mcp-server/server.py

The repository warns about untrusted tool servers — GLOSSARY.md defines MCP, and
infra/terraform-aws/checklists/pre-apply.md says to vet a tool server like a CI plugin — without
ever showing what a trusted one looks like. That is the weaker half of the lesson. This is the
other half: the tool list arrives from a server, and a state-changing tool still cannot run
until a human has approved that specific call.

Speaks a deliberately small subset of MCP's JSON-RPC over stdio: `initialize`, `tools/list`,
`tools/call`. Enough to show the shape, and stdlib-only, so it stays in the dependency-free
`examples` CI job. It is not a conformant MCP implementation and does not try to be — a real
client would need notifications, cancellation, and content-type negotiation this does not have.

The structure of the read/write split is `examples/tool-discovery/`'s, restated here rather than
imported. Two registries, each refusing at register() to hold a tool of the other kind, so the
read path never holds a reference to a write callable in the first place. Restated because an
example that reaches into a sibling for its core mechanism stops being readable on its own, and
because the dependency graph between examples is checked and kept shallow on purpose.

What is new here, and what the tests are about: the tools are *advertised* by the server. A
client discovers `refund_order` exists, sees its schema, and can call it. Discovery is not
authorization, and the gap between the two is the whole subject.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

READ = "read"
WRITE = "write"
ACCESS_LEVELS = (READ, WRITE)

# How long a granted approval stays claimable. Short on purpose: an approval is a human saying
# "yes, this action, now", and one that stays valid for an hour is closer to a standing grant.
APPROVAL_TTL_SECONDS = 300


class ToolError(Exception):
    """A tool could not be run. Carries a JSON-RPC error code."""

    code = -32000


class UnknownTool(ToolError):
    code = -32601


class ApprovalRequired(ToolError):
    """A write tool was called with no approval token at all."""

    code = -32001


class ApprovalInvalid(ToolError):
    """A token was supplied but does not authorize this exact call."""

    code = -32002


class WriteBoundaryViolation(Exception):
    """A registry was asked to hold a tool of the wrong access level.

    Not a ToolError: this is a wiring mistake in the server, not a bad request from a client,
    and it should crash the process at startup rather than become a JSON-RPC error someone
    retries.
    """


@dataclass(frozen=True)
class Tool:
    name: str
    access: str
    description: str
    schema: dict[str, Any]
    run: Callable[..., Any]

    def __post_init__(self) -> None:
        if self.access not in ACCESS_LEVELS:
            raise WriteBoundaryViolation(
                f"tool {self.name!r}: access must be one of {ACCESS_LEVELS}, got {self.access!r}"
            )


class ToolRegistry:
    """Holds tools of exactly one access level, and refuses the other at the door.

    The refusal is in register() rather than at call time on purpose. A registry that accepts
    anything and filters later is one forgotten branch away from running a write tool on the
    read path; a registry that cannot hold the tool has no such branch to forget.
    """

    def __init__(self, access: str) -> None:
        if access not in ACCESS_LEVELS:
            raise ValueError(f"access must be one of {ACCESS_LEVELS}, got {access!r}")
        self.access = access
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> Tool:
        if tool.access != self.access:
            raise WriteBoundaryViolation(
                f"{self.access} registry refused {tool.name!r}, which is {tool.access}"
            )
        self._tools[tool.name] = tool
        return tool

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise UnknownTool(f"no {self.access} tool named {name!r}")
        return self._tools[name]

    def has(self, name: str) -> bool:
        return name in self._tools

    def all(self) -> list[Tool]:
        return [self._tools[n] for n in sorted(self._tools)]

    def __len__(self) -> int:
        return len(self._tools)


def fingerprint(tool_name: str, arguments: dict[str, Any]) -> str:
    """Hash the exact action a human approved.

    `sort_keys` is load-bearing. Without it two dicts that compare equal in Python hash
    differently depending on insertion order, so an approval granted through one code path
    fails to match the identical action arriving by another — intermittently, and looking
    like a race rather than a serialisation bug.
    """
    canonical = json.dumps(
        {"tool": tool_name, "arguments": arguments}, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass
class Approval:
    token: str
    fingerprint: str
    tool: str
    granted_at: float
    used_at: float | None = None


class ApprovalStore:
    """Grants and claims single-use approvals bound to one exact call.

    Bound to the fingerprint rather than to the tool name, because "approve refund_order" and
    "approve refunding order 991 for $4,000" are different promises, and only the second is
    one a human can actually make.
    """

    def __init__(self, clock: Callable[[], float] = time.time) -> None:
        self._clock = clock
        self._approvals: dict[str, Approval] = {}

    def grant(self, tool: str, arguments: dict[str, Any]) -> Approval:
        approval = Approval(
            token=uuid.uuid4().hex,
            fingerprint=fingerprint(tool, arguments),
            tool=tool,
            granted_at=self._clock(),
        )
        self._approvals[approval.token] = approval
        return approval

    def claim(self, token: str, tool: str, arguments: dict[str, Any]) -> Approval:
        approval = self._approvals.get(token)
        if approval is None:
            raise ApprovalInvalid("no such approval token")
        if approval.used_at is not None:
            raise ApprovalInvalid("approval has already been used")
        if self._clock() - approval.granted_at > APPROVAL_TTL_SECONDS:
            raise ApprovalInvalid("approval has expired")
        if approval.fingerprint != fingerprint(tool, arguments):
            raise ApprovalInvalid(
                "approval does not match this call; it was granted for a different action"
            )
        approval.used_at = self._clock()
        return approval


@dataclass
class MCPServer:
    """Dispatches JSON-RPC requests against a read registry and a write registry.

    Holding the two registries as separate fields is the point. `tools/call` cannot resolve a
    name against "the tools" — there is no such collection — so the branch that runs a tool
    without claiming an approval can only ever see read tools.
    """

    read_tools: ToolRegistry
    write_tools: ToolRegistry
    approvals: ApprovalStore
    audit: list[dict[str, Any]] = field(default_factory=list)

    def handle(self, request: dict[str, Any]) -> dict[str, Any] | None:
        method = request.get("method")
        request_id = request.get("id")
        try:
            if method == "initialize":
                result = self._initialize()
            elif method == "tools/list":
                result = self._list_tools()
            elif method == "tools/call":
                result = self._call_tool(request.get("params") or {})
            elif method is not None and method.startswith("notifications/"):
                return None  # Notifications take no response.
            else:
                raise UnknownTool(f"unknown method {method!r}")
        except ToolError as exc:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": exc.code, "message": str(exc)},
            }
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    def _initialize(self) -> dict[str, Any]:
        return {
            "protocolVersion": "2025-06-18",
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "approval-gated-example", "version": "1.0.0"},
        }

    def _list_tools(self) -> dict[str, Any]:
        """Advertise both kinds, and say which ones need an approval.

        Write tools are listed rather than hidden. Hiding them would make the server look safe
        while relying on the client not to guess a name, which is not a boundary — it is an
        absence of documentation. The annotation is a courtesy to a well-behaved client; the
        refusal in _call_tool is what actually holds.
        """
        listed = []
        for tool in self.read_tools.all() + self.write_tools.all():
            listed.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.schema,
                    "annotations": {
                        "readOnlyHint": tool.access == READ,
                        "requiresApproval": tool.access == WRITE,
                    },
                }
            )
        return {"tools": listed}

    def _call_tool(self, params: dict[str, Any]) -> dict[str, Any]:
        name = params.get("name")
        arguments = dict(params.get("arguments") or {})
        token = arguments.pop("approval_token", None)

        if self.read_tools.has(name):
            return self._result(name, self.read_tools.get(name).run(**arguments), approved=False)

        if self.write_tools.has(name):
            if token is None:
                raise ApprovalRequired(
                    f"{name!r} changes state and requires an approval token; "
                    f"request one for these exact arguments first"
                )
            # Claims against the arguments the tool will actually receive, with the token
            # removed. Fingerprinting the dict that still carried the token would let a caller
            # approve one action and execute another by editing a field afterwards.
            self.approvals.claim(token, name, arguments)
            return self._result(name, self.write_tools.get(name).run(**arguments), approved=True)

        raise UnknownTool(f"no tool named {name!r}")

    def _result(self, name: str, value: Any, approved: bool) -> dict[str, Any]:
        self.audit.append({"tool": name, "approved": approved})
        return {"content": [{"type": "text", "text": str(value)}], "isError": False}


# ---------------------------------------------------------------------------
# A small catalogue, so the example runs
# ---------------------------------------------------------------------------

_ORDERS = {"991": {"customer": "acme", "total": 4000.00, "status": "shipped"}}


def _look_up_order(order_id: str) -> str:
    order = _ORDERS.get(order_id)
    return f"order {order_id}: {order}" if order else f"order {order_id}: not found"


def _refund_order(order_id: str, amount: float) -> str:
    return f"refunded {amount} on order {order_id}"


def build_server(approvals: ApprovalStore | None = None) -> MCPServer:
    read_tools = ToolRegistry(READ)
    write_tools = ToolRegistry(WRITE)
    read_tools.register(
        Tool(
            name="look_up_order",
            access=READ,
            description="Return the stored record for one order.",
            schema={
                "type": "object",
                "properties": {"order_id": {"type": "string"}},
                "required": ["order_id"],
            },
            run=_look_up_order,
        )
    )
    write_tools.register(
        Tool(
            name="refund_order",
            access=WRITE,
            description="Refund an amount against an order. Requires an approval token.",
            schema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"},
                    "amount": {"type": "number"},
                    "approval_token": {"type": "string"},
                },
                "required": ["order_id", "amount", "approval_token"],
            },
            run=_refund_order,
        )
    )
    return MCPServer(read_tools, write_tools, approvals or ApprovalStore())


def _demo() -> int:
    server = build_server()
    print("tools/list advertises both kinds:")
    for tool in server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})["result"][
        "tools"
    ]:
        gate = "approval required" if tool["annotations"]["requiresApproval"] else "read-only"
        print(f"  {tool['name']:<16} {gate}")

    call = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": "refund_order", "arguments": {"order_id": "991", "amount": 4000.0}},
    }
    print("\ncalling refund_order with no approval:")
    print(f"  {server.handle(call)['error']['message']}")

    approval = server.approvals.grant("refund_order", {"order_id": "991", "amount": 4000.0})
    print("\nwith an approval granted for a DIFFERENT amount:")
    wrong = json.loads(json.dumps(call))
    wrong["params"]["arguments"] = {
        "order_id": "991",
        "amount": 5000.0,
        "approval_token": approval.token,
    }
    print(f"  {server.handle(wrong)['error']['message']}")

    print("\nwith the approval that matches:")
    call["params"]["arguments"]["approval_token"] = approval.token
    print(f"  {server.handle(call)['result']['content'][0]['text']}")

    print("\nreusing the same token:")
    print(f"  {server.handle(call)['error']['message']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--demo", action="store_true", help="run a scripted walkthrough")
    args = parser.parse_args(argv)
    if args.demo:
        return _demo()

    server = build_server()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            print(
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32700, "message": "parse error"},
                    }
                ),
                flush=True,
            )
            continue
        response = server.handle(request)
        if response is not None:
            print(json.dumps(response), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
