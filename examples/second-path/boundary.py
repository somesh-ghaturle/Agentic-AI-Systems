#!/usr/bin/env python3
"""The write boundary that holds on the path you tested, and the second path to the same effect.

    python3 boundary.py

No dependencies, no model, no key.

---------------------------------------------------------------------------
What this is a small copy of
---------------------------------------------------------------------------

`infra/terraform-aws/tests/` records the real instance. The AWS tree's write boundary was
described as self-enforcing, because a Lambda resource policy carries a precondition that
fails the plan when a write tool is declared with no approval gate in front of it. The
comment atop that test file says what turned out to be wrong with the claim:

    That is true of the resource policy and only of the resource policy. [...] For a caller
    in the SAME ACCOUNT, Lambda grants invocation if the identity policy allows it OR the
    resource policy does.

Two independent grants, and the gate only governs one of them. The orchestrator's identity
policy is built from a list, nothing checked what went into that list, and widening it is a
one-word edit that reads as a simplification.

This module is that shape in about a hundred lines of standard library: a gate that is
correct, a suite that tests it and passes, and a second route to the same effect that never
consults it. The point is not that the gate is weak. The gate here is never wrong. The point
is that being correct is not the same as being *on the path*.

Related: `docs/agentic-system-architecture/ENVIRONMENT-ENGINEERING.md` section 2.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Callable

# The effects, kept as a module-level list so the demonstration can show that a write really
# happened rather than asserting that it was allowed to. A boundary example that only reports
# its own verdict is grading its own homework.
EFFECTS: list[str] = []


class Refused(Exception):
    """Raised when a call is refused. Carries which control refused it, because 'denied' with
    no attribution is the failure this whole example is about."""


@dataclass(frozen=True)
class Tool:
    name: str
    access: str  # "read" or "write" -- nothing else is accepted
    run: Callable[[dict], str]

    def __post_init__(self):
        if self.access not in ("read", "write"):
            raise ValueError(f"{self.name}: access must be 'read' or 'write', got {self.access!r}")


def _read_status(arguments: dict) -> str:
    return f"service {arguments['service']} is healthy"


def _restart(arguments: dict) -> str:
    # The irreversible thing. In the AWS tree this is a Lambda that restarts a service; here it
    # appends to a list, which is enough to tell whether the boundary held.
    EFFECTS.append(f"restarted {arguments['service']}")
    return f"restarted {arguments['service']}"


TOOLS = {
    "get_status": Tool("get_status", "read", _read_status),
    "restart_service": Tool("restart_service", "write", _restart),
}

READ_TOOLS = {name: t for name, t in TOOLS.items() if t.access == "read"}


def fingerprint(name: str, arguments: dict) -> str:
    """Bind an approval to the exact call. sort_keys so the same arguments in a different order
    produce the same claim, and so approving 'restart_service' in the abstract is impossible."""
    payload = json.dumps(
        {"tool": name, "arguments": arguments}, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(payload.encode()).hexdigest()


class ApprovalGate:
    """The control everyone points at. It is correct, and every test below passes against it.

    This is the resource-policy half: it governs calls that arrive *through it*, and it has no
    opinion about calls that do not.
    """

    def execute(self, name: str, arguments: dict, claim: str | None) -> str:
        tool = TOOLS[name]
        if tool.access == "write":
            if claim is None:
                raise Refused("gate: write with no approval claim")
            if claim != fingerprint(name, arguments):
                # Approving one action and executing another is the failure a claim bound to
                # the tool name alone would permit.
                raise Refused("gate: approval claim does not match this call")
        return tool.run(arguments)


class Orchestrator:
    """The identity-policy half: what this component is able to invoke *at all*.

    `reachable` is the list nothing checked. Passing TOOLS instead of READ_TOOLS is the
    one-word edit -- it reads as a simplification, it makes no gate test fail, and it puts a
    second route to the write effect in the system.
    """

    def __init__(self, reachable: dict[str, Tool] | None = None):
        self.reachable = READ_TOOLS if reachable is None else reachable

    def call(self, name: str, arguments: dict) -> str:
        if name not in self.reachable:
            raise Refused("orchestrator: tool not reachable from this component")
        # No claim, no gate. That is not an oversight in this method -- the orchestrator is
        # supposed to be a read-only caller, and for a read-only caller this is correct.
        return self.reachable[name].run(arguments)


def reachable_writes(orchestrator: Orchestrator) -> list[str]:
    """The check that catches it.

    It asks what the component can reach, not what the gate does. Every gate test in the suite
    can pass while this returns a non-empty list, which is the whole lesson: a control with two
    enforcement points and one test has one enforcement point.
    """
    return sorted(n for n, t in orchestrator.reachable.items() if t.access == "write")


def _demo() -> None:
    args = {"service": "billing"}

    print("1. The gate, tested directly -- this is the suite everyone writes\n")
    gate = ApprovalGate()
    for label, claim in (("no claim", None), ("wrong claim", fingerprint("restart_service", {}))):
        try:
            gate.execute("restart_service", args, claim)
            print(f"   {label:<12} ALLOWED  <- would be a bug")
        except Refused as exc:
            print(f"   {label:<12} refused  ({exc})")
    approved = gate.execute("restart_service", args, fingerprint("restart_service", args))
    print(f"   valid claim  allowed  ({approved})")
    print("\n   The gate is correct. Nothing below changes that.\n")

    print("2. The orchestrator as designed -- reachable set is the read tools\n")
    EFFECTS.clear()
    try:
        Orchestrator().call("restart_service", args)
        print("   restart_service ALLOWED  <- would be a bug")
    except Refused as exc:
        print(f"   restart_service refused  ({exc})")
    print(f"   effects: {EFFECTS}")
    print(f"   reachable writes: {reachable_writes(Orchestrator())}\n")

    print("3. The one-word edit -- READ_TOOLS becomes TOOLS\n")
    EFFECTS.clear()
    wide = Orchestrator(TOOLS)
    result = wide.call("restart_service", args)
    print(f"   restart_service ALLOWED  ({result})")
    print(f"   effects: {EFFECTS}")
    print("   The gate was never consulted. It did not fail -- it was not on the path.")
    print(f"   reachable writes: {reachable_writes(wide)}  <- the check that catches it")


if __name__ == "__main__":
    _demo()
