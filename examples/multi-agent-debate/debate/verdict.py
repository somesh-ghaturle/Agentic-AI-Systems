"""What a debate produces — and the one thing it deliberately does not.

The temptation in a multi-agent design is to add an "approver" agent: proposer argues,
critic objects, approver decides, done. It reads as the natural third role and it is the
one mistake this example exists to refuse.

An agent that can approve an agent's proposal is not an authorization step. It is the same
untrusted output wearing a different hat, and every property the approval gate is supposed
to provide — that a state-changing action cannot reach production without a *human*
authorizing that specific action — is gone the moment the approving principal is another
model. `infra/*/modules/approval` spells this out in Terraform: the executor role is
deliberately never granted the APPROVE procedure, because a machine role that can approve
its own proposal collapses the gate into a formality.

So a `Verdict` carries no approval, and `requires_human_approval` is a read-only property
that is always True. There is no constructor argument that changes it, because a flag that
can be set is a flag that will be.

What a debate *does* produce is a better proposal and an honest record of what was not
resolved. That is worth having. It is not authorization.
"""

from __future__ import annotations

from dataclasses import dataclass

from .transcript import Transcript


@dataclass(frozen=True)
class Dissent:
    """An objection that was never answered."""

    speaker: str
    rationale: str


@dataclass(frozen=True)
class Verdict:
    """The outcome of a debate. Deliberately not a decision."""

    proposal: dict
    transcript: Transcript
    rounds_used: int

    #: True when every critic ended on SUPPORT. False when the round budget ran out with
    #: objections outstanding, or when the proposer declined to revise further.
    converged: bool

    #: Objections still standing at the end. Non-empty means the panel did not agree, and
    #: that fact travels with the proposal to whoever reviews it.
    dissent: tuple[Dissent, ...] = ()

    @property
    def requires_human_approval(self) -> bool:
        """Always True.

        A property rather than a field so that no call site can construct a Verdict that
        claims otherwise. If a future change needs an auto-approve path, it needs a
        different type and a conversation, not an argument here.
        """
        return True

    @property
    def unanimous(self) -> bool:
        return self.converged and not self.dissent

    def summary(self) -> str:
        rounds = f"{self.rounds_used} round(s)"
        if self.unanimous:
            state = f"converged in {rounds}, no dissent"
        elif self.converged:
            state = f"converged in {rounds}, {len(self.dissent)} dissent(s) recorded"
        else:
            state = f"did NOT converge in {rounds}, {len(self.dissent)} objection(s) standing"
        action = self.proposal.get("action", "<no action>")
        return f"{action}: {state} — human approval still required"
