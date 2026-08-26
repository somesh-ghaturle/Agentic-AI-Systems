#!/usr/bin/env python3
"""The demo: three debates that end three different ways.

Run it:

    python3 agent.py

The participants here are scripted rather than model-backed, and that is the design
decision that makes this example testable at all. A debate protocol's guarantees are
properties of the protocol — it either records surviving dissent or it does not, it either
stops at the round budget or it does not — so putting a model behind the roles would make
every run different without testing anything extra. It is the same move `harness-agent`
makes with its verifier and `trace-eval` makes with its graders.

Swapping in real model calls means implementing the three Protocols in `debate.panel`.
Nothing else changes.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from debate import Panel, Position, Role, Turn, run_debate


class ScriptedProposer:
    """Proposes a refund, and concedes at most once."""

    def __init__(self, name="proposer", concessions=1):
        self.name = name
        self._concessions = concessions

    def propose(self, goal):
        return {
            "action": "process_refund",
            "arguments": {"order_id": "A-1174", "amount_cents": 45_00},
            "rationale": f"customer requested: {goal}",
        }

    def revise(self, proposal, transcript):
        if self._concessions <= 0:
            return None
        self._concessions -= 1
        revised = dict(proposal)
        revised["arguments"] = dict(proposal["arguments"], amount_cents=25_00)
        revised["rationale"] = "reduced to the documented ceiling after the cost objection"
        return revised


class ScriptedCritic:
    """Opposes until a condition on the proposal is met, then supports."""

    def __init__(self, name, perspective, satisfied_when, objection, assent):
        self.name = name
        self.perspective = perspective
        self._satisfied_when = satisfied_when
        self._objection = objection
        self._assent = assent

    def critique(self, proposal, transcript, round_number):
        ok = self._satisfied_when(proposal)
        return Turn(
            round=round_number,
            role=Role.CRITIC,
            speaker=self.name,
            position=Position.SUPPORT if ok else Position.OPPOSE,
            rationale=self._assent if ok else self._objection,
            proposal=dict(proposal),
        )


class ScriptedArbiter:
    """Calls the debate when no critic is still opposing."""

    name = "arbiter"

    def converged(self, proposal, transcript):
        speakers = {t.speaker for t in transcript.turns if t.role is Role.CRITIC}
        return all(transcript.last_position(s) is not Position.OPPOSE for s in speakers)


def _cost_ok(proposal):
    return proposal["arguments"]["amount_cents"] <= 25_00


def _always(_proposal):
    return True


def _never(_proposal):
    return False


def SAFETY_OK():
    """A critic that is always satisfied — the refund is reversible."""
    return ScriptedCritic(
        "safety", "safety", _always,
        objection="an irreversible action would need a second reviewer",
        assent="refund is reversible; no safety concern",
    )


def COST_CEILING():
    """A critic satisfied only once the amount is under the documented ceiling."""
    return ScriptedCritic(
        "cost", "cost", _cost_ok,
        objection="45.00 exceeds the 25.00 auto-refund ceiling",
        assent="within the documented ceiling",
    )


def POLICY_NEVER():
    """A critic nothing satisfies. Its objection is what the round budget runs out against."""
    return ScriptedCritic(
        "policy", "policy", _never,
        objection="no written policy covers this order type",
        assent="a policy would have to exist first",
    )


def _run(title, panel, goal, max_rounds):
    print(f"\n{'=' * 72}\n{title}\n{'=' * 72}")
    verdict = run_debate(panel, goal, max_rounds=max_rounds)

    for turn in verdict.transcript.turns:
        print(f"  r{turn.round} {turn.speaker:<10} {turn.position.value:<8} {turn.rationale}")

    print(f"\n  {verdict.summary()}")
    if verdict.dissent:
        for d in verdict.dissent:
            print(f"  DISSENT  {d.speaker}: {d.rationale}")
    print(f"  requires_human_approval = {verdict.requires_human_approval}")
    return verdict


def main():
    # 1 — the panel converges after the proposer concedes on cost.
    _run(
        "1. Convergence after a concession",
        Panel(
            proposer=ScriptedProposer(concessions=1),
            critics=(SAFETY_OK(), COST_CEILING()),
            arbiter=ScriptedArbiter(),
        ),
        goal="refund order A-1174",
        max_rounds=3,
    )

    # 2 — the proposer stands pat. Honest non-agreement, and the objection survives.
    _run(
        "2. Proposer stands pat — dissent recorded, not resolved",
        Panel(
            proposer=ScriptedProposer(concessions=0),
            critics=(SAFETY_OK(), COST_CEILING()),
            arbiter=ScriptedArbiter(),
        ),
        goal="refund order A-1174",
        max_rounds=3,
    )

    # 3 — an unsatisfiable critic. The budget runs out and that is NOT convergence.
    _run(
        "3. Budget exhausted — converged is False",
        Panel(
            proposer=ScriptedProposer(concessions=99),
            critics=(SAFETY_OK(), POLICY_NEVER()),
            arbiter=ScriptedArbiter(),
        ),
        goal="refund order A-1174",
        max_rounds=2,
    )

    print(
        "\nAll three verdicts require human approval. A debate improves a proposal and\n"
        "records what was not resolved. It does not authorize anything — see debate/verdict.py.\n"
    )


if __name__ == "__main__":
    main()
