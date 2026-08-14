#!/usr/bin/env python3
"""Hermes CLI — send it a request and watch where it goes.

    python3 examples/hermes-agent/agent.py "summarize incident-2291"
    python3 examples/hermes-agent/agent.py "restart the billing service"
    python3 examples/hermes-agent/agent.py --approve "restart the billing service"

Without `--approve`, a request that would change something stops at a proposal and prints
what a human is being asked to authorise. With it, the script grants an approval for that
exact action and hands it to the executor — standing in for a person clicking approve.

Nothing here reaches the network and there is nothing to install.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from hermes import Tracer, stdout_sink
from hermes.demo import build_agent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="hermes",
        description="Route a request; stop at the write boundary unless approved.",
    )
    parser.add_argument("request", nargs="*", help="the request, in plain words")
    parser.add_argument(
        "--approve",
        action="store_true",
        help="stand in for a human approving the proposed write, then execute it",
    )
    parser.add_argument(
        "--approver",
        default="demo-operator",
        help="name recorded on the approval (default: demo-operator)",
    )
    parser.add_argument(
        "--quiet", action="store_true", help="suppress the trace on stderr"
    )
    parser.add_argument(
        "--json", action="store_true", help="print the result as JSON instead of prose"
    )
    args = parser.parse_args(argv)

    request = " ".join(args.request) or input("Request: ")

    agent, executor = build_agent()
    tracer = Tracer(sink=None if args.quiet else stdout_sink)
    result = agent.handle(request, tracer=tracer)

    if not result.pending:
        _report(
            args,
            {
                "trace_id": result.trace_id,
                "intent": result.intent,
                "handler": result.handler,
                "status": "completed",
                "output": result.output,
            },
        )
        return 0

    proposal = result.proposal
    payload: dict[str, Any] = {
        "trace_id": result.trace_id,
        "intent": result.intent,
        "handler": result.handler,
        "status": "awaiting approval",
        "proposed_tool": proposal.tool,
        "arguments": proposal.arguments,
        "rationale": proposal.rationale,
        "fingerprint": proposal.fingerprint,
    }

    if not args.approve:
        payload["next_step"] = "re-run with --approve to authorise exactly this action"
        _report(args, payload)
        # 2 rather than 0: a pending write is not a completed request, and a caller
        # scripting this should be able to tell the difference without parsing output.
        return 2

    approval = agent.approvals.grant(
        proposal.tool, proposal.arguments, approver=args.approver
    )
    payload["status"] = "executed"
    payload["approved_by"] = approval.approver
    payload["output"] = executor.execute(proposal, approval.token, tracer=tracer)
    _report(args, payload)
    return 0


def _report(args: argparse.Namespace, payload: dict[str, Any]) -> None:
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    print(f"trace   {payload['trace_id']}")
    print(f"intent  {payload['intent']} → {payload['handler']}()")
    print(f"status  {payload['status']}")
    if "proposed_tool" in payload:
        rendered = ", ".join(
            f"{key}={value!r}" for key, value in sorted(payload["arguments"].items())
        )
        print(f"write   {payload['proposed_tool']}({rendered})")
        print(f"why     {payload['rationale']}")
        print(f"digest  {payload['fingerprint'][:16]}…")
    if payload.get("approved_by"):
        print(f"by      {payload['approved_by']}")
    if "next_step" in payload:
        print(f"next    {payload['next_step']}")
    if payload.get("output") is not None:
        print(f"result  {json.dumps(payload['output'], sort_keys=True)}")


if __name__ == "__main__":
    sys.exit(main())
