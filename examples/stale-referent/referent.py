#!/usr/bin/env python3
"""An approval binds the request. The effect depends on the request and the world it names.

    python3 referent.py

No dependencies, no model, no key.

---------------------------------------------------------------------------
The property this example is about
---------------------------------------------------------------------------

`second-path` is about a second route to an effect: the gate is correct and simply not on the
path taken. `tool-discovery` is about a filter where a structure was needed. This one is
narrower and, in a system that has fixed both of those, more likely:

    The call that was approved and the call that ran are byte-identical.
    The fingerprint matches. The gate is consulted, and it allows the call.
    A different thing happens.

Because arguments are usually references, not values. A human approves `refund(order="A-42")`
after being shown "$50.00, order A-42, customer c-1". The refund tool resolves A-42 against
the ledger when it runs. Between those two moments the ledger is a shared, mutable thing that
other parts of the system -- including the agent -- are still writing to.

Nothing here is a bypass. Every control does exactly what it says.

---------------------------------------------------------------------------
Why a fingerprint does not catch it
---------------------------------------------------------------------------

`infra/*/src/shared/contracts.py` hashes the action and the arguments a human approved, and
the executor re-checks that hash before it runs. That check is worth having and it is the
wrong shape for this failure: the arguments did not change. `{"order": "A-42"}` hashes the
same before and after the amount on A-42 moves from $50 to $5,000.

A hash over a reference certifies the reference, not the thing referred to.

Related: `docs/agentic-system-architecture/ENVIRONMENT-ENGINEERING.md` section 2, and
`examples/second-path/` for the other way a correct gate stops mattering.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

# The world. Shared, mutable, and read by the tool at the moment it runs -- which is the only
# property this example needs it to have. In a real system it is a database row, a feature
# flag, a price list, or a group membership.
LEDGER: dict[str, dict] = {
    "A-42": {"amount_cents": 5_000, "customer": "c-1", "status": "open"},
}

# Effects, so the demonstration can show what happened rather than what was permitted.
EFFECTS: list[str] = []


class Refused(Exception):
    """Carries which control refused and why. 'Denied' with no attribution is unactionable."""


def fingerprint(tool: str, arguments: dict) -> str:
    """The same canonical form the three infrastructure trees use.

    Correct, and not sufficient here: it hashes what was asked for, and what was asked for is
    a reference.
    """
    payload = json.dumps(
        {"tool": tool, "arguments": arguments}, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def resolve(arguments: dict) -> dict:
    """The facts a reviewer is shown: what this call means *right now*.

    This is the function whose output changes while the arguments do not.
    """
    order = LEDGER[arguments["order"]]
    return {"amount_cents": order["amount_cents"], "customer": order["customer"]}


@dataclass(frozen=True)
class Approval:
    tool: str
    arguments: dict
    claim: str
    # What the reviewer actually saw. Recorded because a decision is made about the resolved
    # facts, not about the reference -- nobody approves "refund A-42" without being told what
    # A-42 is. Recording it costs one field; not recording it is this whole example.
    shown: dict = field(default_factory=dict)


class ApprovalGate:
    """The control. It is correct, and every test written against it passes.

    It binds the call: a write needs a claim, and the claim must be this exact call's
    fingerprint. Approving a refund and executing a restart is refused. Approving a refund of
    one order and executing another is refused.
    """

    def review(self, tool: str, arguments: dict) -> Approval:
        """What a reviewer is given, and what is recorded when they approve."""
        return Approval(
            tool=tool,
            arguments=dict(arguments),
            claim=fingerprint(tool, arguments),
            shown=resolve(arguments),
        )

    def execute(self, tool: str, arguments: dict, claim: str | None) -> str:
        if claim is None:
            raise Refused("gate: write with no approval claim")
        if claim != fingerprint(tool, arguments):
            raise Refused("gate: approval claim does not match this call")
        return _refund(arguments)


def _refund(arguments: dict) -> str:
    """The irreversible thing. It resolves the reference when it runs, which is correct
    behaviour for a refund tool and is the moment the two worlds can differ."""
    order = LEDGER[arguments["order"]]
    EFFECTS.append(f"refunded {order['amount_cents']} to {order['customer']}")
    return f"refunded {order['amount_cents']} cents"


def drift(approval: Approval) -> dict[str, tuple]:
    """The check that catches it.

    It asks whether the facts the decision was made about still hold, not whether the call is
    the one that was approved. Every gate test can pass while this returns a non-empty dict,
    which is the lesson: a control that binds the request does not bind the outcome.
    """
    now = resolve(approval.arguments)
    return {
        key: (approval.shown[key], now[key])
        for key in approval.shown
        if approval.shown[key] != now[key]
    }


def execute_bound(gate: ApprovalGate, approval: Approval) -> str:
    """Execute only if the world still matches the decision.

    The refusal names the field that moved, because "approval no longer valid" sends an
    operator to re-approve the same thing rather than to ask what changed underneath it.
    """
    moved = drift(approval)
    if moved:
        detail = ", ".join(f"{k}: {was} -> {now}" for k, (was, now) in sorted(moved.items()))
        raise Refused(f"binding: approved facts no longer hold ({detail})")
    return gate.execute(approval.tool, approval.arguments, approval.claim)


def _demo() -> None:
    gate = ApprovalGate()
    args = {"order": "A-42"}

    print("1. The gate, tested directly -- the suite everyone writes\n")
    for label, claim in (
        ("no claim", None),
        ("other order", fingerprint("refund", {"order": "B-7"})),
    ):
        try:
            gate.execute("refund", args, claim)
            print(f"   {label:<12} ALLOWED  <- would be a bug")
        except Refused as exc:
            print(f"   {label:<12} refused  ({exc})")

    EFFECTS.clear()
    approval = gate.review("refund", args)
    print(f"\n   reviewer saw: {approval.shown}")
    print(f"   valid claim  allowed  ({gate.execute('refund', args, approval.claim)})")
    print(f"   effects: {EFFECTS}")
    print("\n   The gate is correct. Nothing below changes that.\n")

    print("2. The same approval, after the ledger moves\n")
    EFFECTS.clear()
    approval = gate.review("refund", args)
    print(f"   reviewer saw: {approval.shown}")
    LEDGER["A-42"]["amount_cents"] = 500_000  # a price correction, a bug, or the agent itself
    print("   ledger changed: amount_cents 5000 -> 500000")
    result = gate.execute("refund", args, approval.claim)
    print(f"   same call, same claim: ALLOWED  ({result})")
    print(f"   effects: {EFFECTS}")
    print("   The claim matched because the arguments never changed.")
    print(f"   drift: {drift(approval)}  <- the check that catches it\n")

    print("3. Bound to the facts the decision was made about\n")
    EFFECTS.clear()
    try:
        execute_bound(gate, approval)
        print("   ALLOWED  <- would be a bug")
    except Refused as exc:
        print(f"   refused  ({exc})")
    print(f"   effects: {EFFECTS}")

    LEDGER["A-42"]["amount_cents"] = 5_000


if __name__ == "__main__":
    _demo()
