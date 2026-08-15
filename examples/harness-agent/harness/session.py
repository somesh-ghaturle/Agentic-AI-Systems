"""One session, one feature.

A session stands in for a context window. The constraint it enforces is the one that maps to
the "over-ambition" failure mode: an agent that decides to implement four features because
they are all small runs out of context on the third and leaves the environment in a state the
next session has to reconstruct.

The fix is not a prompt asking it to be careful. It is that `claim` can be called once per
session and raises the second time. The agent is free to want more work; the harness is what
decides it does not get it.

The second constraint here is the step budget, which is the ordinary bounded-loop rule applied
at session scope — see BUILDING-BLOCKS §4 and ARCHITECTURE-PATTERNS in docs/ for why every
loop in an agentic system carries one.
"""

from . import state as st


class SessionError(Exception):
    """Raised when a session is asked to do something its contract forbids."""


class Session:
    """A single context window's worth of work.

    Not reusable. Once closed, every method raises — a session object that keeps working after
    its window ended is a lie about where the boundary is, and the tests assert it does not.
    """

    def __init__(self, progress, verifier, max_steps=8):
        if max_steps < 1:
            raise SessionError("max_steps must be at least 1")
        self.progress = progress
        self.verifier = verifier
        self.max_steps = max_steps
        self.steps = 0
        self.claimed = None
        self.closed = False
        self._log = []

    # -- lifecycle ----------------------------------------------------------------

    def _check_open(self):
        if self.closed:
            raise SessionError("this session is closed; start a new one")

    def _spend(self, what):
        """Charge one step against the budget.

        Charged before the work, not after. Charging after would let the final step exceed the
        budget and still count as legal, which makes the bound advisory.
        """
        self._check_open()
        if self.steps >= self.max_steps:
            raise SessionError(
                f"step budget exhausted ({self.max_steps}); close the session and resume"
            )
        self.steps += 1
        self._log.append(what)

    @property
    def log(self):
        return list(self._log)

    def close(self):
        self.closed = True

    # -- the three things a session can do ----------------------------------------

    def claim(self, feature):
        """Take exactly one feature for this session."""
        self._check_open()
        if self.claimed is not None:
            raise SessionError(
                f"session already claimed {self.claimed!r}; one feature per session. "
                f"Close this session and open another for {feature!r}"
            )
        if self.progress.state(feature) != st.PENDING:
            raise SessionError(
                f"{feature!r} is {self.progress.state(feature)!r}, not {st.PENDING!r}"
            )
        self._spend(f"claim:{feature}")
        self.progress.advance(feature, st.CLAIMED)
        self.claimed = feature
        return feature

    def verify(self):
        """Run the verifier against the claimed feature.

        Returns the verifier's result. Only a pass advances the feature — and note that the
        harness does not ask the agent whether the work is done. It asks the verifier. That
        distinction is the whole of the "incomplete testing" failure mode.
        """
        self._check_open()
        if self.claimed is None:
            raise SessionError("nothing claimed in this session; call claim() first")
        if self.progress.state(self.claimed) != st.CLAIMED:
            raise SessionError(
                f"{self.claimed!r} is {self.progress.state(self.claimed)!r}; "
                "verify() runs on a claimed feature"
            )
        self._spend(f"verify:{self.claimed}")
        result = self.verifier(self.claimed)
        if result.passed:
            self.progress.advance(self.claimed, st.VERIFIED)
        return result

    def mark_complete(self):
        """Move a verified feature to complete.

        Separate from `verify` on purpose. Completion is a claim about the recorded state of
        the world, and `advance` will refuse this transition from CLAIMED — so a session that
        skips verification cannot reach COMPLETE even by calling this directly.
        """
        self._check_open()
        if self.claimed is None:
            raise SessionError("nothing claimed in this session")
        self._spend(f"complete:{self.claimed}")
        self.progress.advance(self.claimed, st.COMPLETE)
        return self.claimed
