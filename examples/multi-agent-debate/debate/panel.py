"""The participants, and the two ways a panel is worse than no panel at all.

A debate is only worth its cost if the participants can actually disagree. Two failure
modes make that false while leaving everything looking correct:

**A panel of clones.** Run the same model with the same prompt three times and you have one
opinion reported three times. The transcript shows unanimous support, which reads as a
strong signal and is a measurement of nothing. `Panel` refuses to build itself from critics
that declare the same perspective.

**An arbiter that also argues.** If whoever judges convergence is also advancing a position,
the debate concludes when that participant is satisfied with their own proposal. This is the
same separation the write boundary makes between the principal that proposes and the
principal that authorizes, one layer up — and it is enforced here for the same reason: it is
invisible when it is wrong.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .transcript import Position, Role, Transcript, Turn


class DegeneratePanel(Exception):
    """Raised when a panel cannot produce disagreement."""


class RoleViolation(Exception):
    """Raised when a participant speaks outside its role."""


class Proposer(Protocol):
    """Puts something forward, and may revise it in response to criticism."""

    name: str

    def propose(self, goal: str) -> dict: ...

    def revise(self, proposal: dict, transcript: Transcript) -> dict | None:
        """Return a revised proposal, or None to stand pat.

        Standing pat is a legitimate outcome and ends the debate — a proposer that revises
        forever produces convergence by exhaustion rather than by agreement.
        """


class Critic(Protocol):
    """Argues for or against the proposal on the table."""

    name: str

    #: What this critic is looking at — "safety", "cost", "correctness". Two critics
    #: sharing a perspective is what DegeneratePanel exists to catch.
    perspective: str

    def critique(self, proposal: dict, transcript: Transcript, round_number: int) -> Turn:
        """Return a Turn stamped with `round_number`.

        The round is handed in rather than inferred from the transcript. A critic that
        works out its own round number gets it wrong the first time the protocol changes
        how many turns precede it, and the resulting off-by-one silently reorders
        `last_position` — which is what dissent is computed from.
        """


class Arbiter(Protocol):
    """Judges whether the debate has finished. Advances no position of its own."""

    name: str

    def converged(self, proposal: dict, transcript: Transcript) -> bool: ...


@dataclass
class Panel:
    """A proposer, two or more critics with distinct perspectives, and an arbiter."""

    proposer: Proposer
    critics: tuple[Critic, ...]
    arbiter: Arbiter

    def __post_init__(self):
        if len(self.critics) < 2:
            raise DegeneratePanel(
                f"a panel needs at least two critics; got {len(self.critics)}. "
                "One critic is a review, not a debate — there is nothing for the arbiter to weigh."
            )

        perspectives = [c.perspective for c in self.critics]
        if len(set(perspectives)) != len(perspectives):
            raise DegeneratePanel(
                f"critics do not have distinct perspectives: {perspectives}. "
                "Identical critics produce one opinion reported N times, and unanimous "
                "support from them measures nothing."
            )

        # Role collisions are checked before the generic duplicate-name check below, and
        # the order is deliberate: both would fire on the same input, but "the arbiter is
        # also the proposer" tells the reader what is actually wrong, while "names are not
        # distinct" sends them looking for a typo.
        if self.arbiter.name == self.proposer.name:
            raise RoleViolation(
                "the arbiter and the proposer are the same participant; the debate would "
                "end when the proposer is satisfied with their own proposal"
            )

        if any(self.arbiter.name == c.name for c in self.critics):
            raise RoleViolation(
                "the arbiter is also a critic; whoever judges convergence must not be "
                "advancing a position in the argument being judged"
            )

        names = [self.proposer.name, self.arbiter.name, *(c.name for c in self.critics)]
        if len(set(names)) != len(names):
            # Shared names would silently merge two participants' turns in
            # Transcript.by_speaker, which is what dissent is computed from.
            raise DegeneratePanel(f"participants do not have distinct names: {names}")

    def check_turn(self, turn: Turn) -> Turn:
        """Reject a turn that speaks outside its role.

        The arbiter judging convergence is the role that matters. An arbiter emitting a
        PROPOSE or an OPPOSE has stopped judging and started arguing, and nothing
        downstream would notice.
        """
        if turn.role is Role.ARBITER and turn.position is not Position.SUPPORT:
            raise RoleViolation(
                f"arbiter {turn.speaker} took position {turn.position.value}; an arbiter "
                "judges whether the debate is finished and advances no position of its own"
            )
        if turn.role is Role.CRITIC and turn.position is Position.PROPOSE:
            raise RoleViolation(
                f"critic {turn.speaker} issued a proposal; only the proposer proposes, or "
                "the panel has no consistent thing to argue about"
            )
        return turn
