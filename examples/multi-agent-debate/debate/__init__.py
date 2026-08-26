"""Multi-agent debate: a way to improve a proposal, not a way to authorize one.

Read `verdict.py` first. It is the shortest module and it carries the decision the rest of
the package is arranged around — that a debate never produces an approval.
"""

from .panel import Arbiter, Critic, DegeneratePanel, Panel, Proposer, RoleViolation
from .protocol import DebateError, run_debate
from .transcript import Position, Role, Transcript, TranscriptClosed, Turn
from .verdict import Dissent, Verdict

__all__ = [
    "Arbiter",
    "Critic",
    "DebateError",
    "DegeneratePanel",
    "Dissent",
    "Panel",
    "Position",
    "Proposer",
    "Role",
    "RoleViolation",
    "Transcript",
    "TranscriptClosed",
    "Turn",
    "Verdict",
    "run_debate",
]
