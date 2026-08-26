"""The record of what was argued, and why it cannot be edited afterwards.

A debate's output is not the conclusion. It is the conclusion *plus the disagreement that
survived it* — and the second half is the part a system under review will be asked for. If
the transcript can be rewritten once the outcome is known, it records agreement that may
never have happened, and the debate becomes a way of manufacturing consensus rather than
testing one.

So the transcript here is append-only, and closed transcripts reject appends. Both are
enforced rather than documented: `Turn` is frozen, the internal list is never handed out,
and `close()` is one-way.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field


class Position(enum.Enum):
    """What a participant is saying about the proposal on the table."""

    SUPPORT = "support"
    OPPOSE = "oppose"
    REVISE = "revise"

    #: The proposer putting something forward. Not an opinion about it.
    PROPOSE = "propose"


class Role(enum.Enum):
    """Who is speaking.

    The separation between ARBITER and the other two is the whole point of the type — see
    `debate.panel` for what it costs to blur it.
    """

    PROPOSER = "proposer"
    CRITIC = "critic"
    ARBITER = "arbiter"


class TranscriptClosed(Exception):
    """Raised on any attempt to append to a closed transcript."""


@dataclass(frozen=True)
class Turn:
    """One contribution. Frozen: a turn is a historical fact, not a working value."""

    round: int
    role: Role
    speaker: str
    position: Position
    rationale: str

    #: The proposal as it stood when this turn was taken. Carried per-turn rather than
    #: looked up later, because "what were they actually objecting to" is unanswerable
    #: once the proposal has moved on and only the final version survives.
    proposal: dict | None = None

    def __post_init__(self):
        if self.round < 0:
            raise ValueError(f"round must be non-negative, got {self.round}")
        if not self.rationale.strip():
            # An objection with no reason cannot be answered, and a support with no reason
            # is indistinguishable from not having read the proposal. Neither belongs in a
            # record whose purpose is to be reviewed later.
            raise ValueError(f"{self.speaker} gave a {self.position.value} with no rationale")


@dataclass
class Transcript:
    """Append-only sequence of turns."""

    _turns: list[Turn] = field(default_factory=list, repr=False)
    _closed: bool = field(default=False, repr=False)

    def append(self, turn: Turn) -> None:
        if self._closed:
            raise TranscriptClosed(
                f"transcript is closed; {turn.speaker} cannot add a "
                f"{turn.position.value} after the verdict was reached"
            )
        self._turns.append(turn)

    def close(self) -> None:
        """One-way. There is deliberately no reopen()."""
        self._closed = True

    @property
    def closed(self) -> bool:
        return self._closed

    @property
    def turns(self) -> tuple[Turn, ...]:
        """A tuple, not the list.

        Returning the list would let a caller mutate history through the back door while
        every append() guard above still passed.
        """
        return tuple(self._turns)

    def by_speaker(self, speaker: str) -> tuple[Turn, ...]:
        return tuple(t for t in self._turns if t.speaker == speaker)

    def last_position(self, speaker: str) -> Position | None:
        """The position a participant ended on.

        This is what dissent is computed from. A critic who opposed in round one and was
        satisfied by a revision in round two is not a dissenter; a critic who opposed and
        was never answered is.
        """
        turns = self.by_speaker(speaker)
        return turns[-1].position if turns else None

    def rounds(self) -> int:
        return max((t.round for t in self._turns), default=0)

    def __len__(self) -> int:
        return len(self._turns)
