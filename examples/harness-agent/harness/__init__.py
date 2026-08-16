"""A harness for an agent that outlives its context window.

Four modules, one idea each:

    state.py    the progress file, and the transitions it will accept
    session.py  one context window, one feature, a step budget
    verify.py   evidence the agent does not produce and cannot edit
    runner.py   sessions in sequence, persisted between them

Read state.py first. Everything else is arranged around the guarantee it makes.
"""

from .runner import Harness, HarnessError
from .session import Session, SessionError
from .state import (
    CLAIMED,
    COMPLETE,
    PENDING,
    VERIFIED,
    Progress,
    StateError,
    load,
    save,
)
from .verify import AlwaysPasses, CommandVerifier, Result, ScriptedVerifier

__all__ = [
    "CLAIMED",
    "COMPLETE",
    "PENDING",
    "VERIFIED",
    "AlwaysPasses",
    "CommandVerifier",
    "Harness",
    "HarnessError",
    "Progress",
    "Result",
    "ScriptedVerifier",
    "Session",
    "SessionError",
    "StateError",
    "load",
    "save",
]
