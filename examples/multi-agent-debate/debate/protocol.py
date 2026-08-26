"""The loop: bounded rounds, and what happens when the budget runs out.

The rule that matters most here is that **running out of rounds is not convergence.** It is
the easiest thing in the world to write a loop that argues until `max_rounds` and then
returns the last proposal as though the panel agreed on it — the code is shorter, the tests
pass, and the failure is invisible because a non-converged verdict and a converged one look
identical downstream.

So `run_debate` distinguishes three endings, and the caller can tell them apart:

    converged=True,  dissent=()        every critic ended on SUPPORT
    converged=True,  dissent=(...)     the arbiter called it, objections outstanding
    converged=False, dissent=(...)     the budget ran out, or the proposer stood pat

Only the first is agreement. All three still require a human to authorize the action, which
is `Verdict.requires_human_approval` and is not negotiable — see `debate.verdict`.
"""

from __future__ import annotations

from .panel import Panel
from .transcript import Position, Role, Transcript, Turn
from .verdict import Dissent, Verdict


class DebateError(Exception):
    """Raised when the protocol itself is misused."""


def run_debate(panel: Panel, goal: str, max_rounds: int = 3) -> Verdict:
    """Run a bounded debate and return what survived it.

    `max_rounds` is a budget, not a target. A debate that converges in one round is a good
    outcome, not a wasted panel.
    """
    if max_rounds < 1:
        raise DebateError(f"max_rounds must be at least 1, got {max_rounds}")

    transcript = Transcript()

    proposal = panel.proposer.propose(goal)
    if not isinstance(proposal, dict) or "action" not in proposal:
        raise DebateError(
            f"proposer {panel.proposer.name} returned {proposal!r}; a proposal must be a "
            "dict naming an action"
        )

    transcript.append(
        Turn(
            round=0,
            role=Role.PROPOSER,
            speaker=panel.proposer.name,
            position=Position.PROPOSE,
            rationale=proposal.get("rationale", "initial proposal"),
            proposal=dict(proposal),
        )
    )

    converged = False
    rounds_used = 0

    for round_number in range(1, max_rounds + 1):
        rounds_used = round_number

        for critic in panel.critics:
            turn = panel.check_turn(critic.critique(proposal, transcript, round_number))
            if turn.round != round_number:
                # A turn stamped with the wrong round corrupts last_position ordering and
                # therefore the dissent computation. Caught here rather than trusted.
                raise DebateError(
                    f"critic {critic.name} returned a turn stamped round {turn.round} "
                    f"during round {round_number}"
                )
            transcript.append(turn)

        if panel.arbiter.converged(proposal, transcript):
            converged = True
            break

        revision = panel.proposer.revise(proposal, transcript)
        if revision is None:
            # Standing pat ends the debate without convergence. The proposer has heard the
            # objections and declined to move; that is a legitimate position and an honest
            # non-agreement, not a failure to be retried.
            break

        proposal = revision
        transcript.append(
            Turn(
                round=round_number,
                role=Role.PROPOSER,
                speaker=panel.proposer.name,
                position=Position.REVISE,
                rationale=proposal.get("rationale", "revised after criticism"),
                proposal=dict(proposal),
            )
        )

    dissent = tuple(
        Dissent(speaker=c.name, rationale=_last_rationale(transcript, c.name))
        for c in panel.critics
        if transcript.last_position(c.name) is Position.OPPOSE
    )

    transcript.close()

    return Verdict(
        proposal=proposal,
        transcript=transcript,
        rounds_used=rounds_used,
        converged=converged,
        dissent=dissent,
    )


def _last_rationale(transcript: Transcript, speaker: str) -> str:
    turns = transcript.by_speaker(speaker)
    return turns[-1].rationale if turns else ""
