"""The runner: sessions in sequence, state on disk between them.

This is the piece that makes the other three modules a harness rather than three utilities.
It owns the resume-or-start decision, opens one session per feature, persists after every
transition, and refuses to declare the work finished on anyone's say-so but the progress
file's.

The persistence placement is the load-bearing detail. `save` runs after each state change
rather than at the end of a session, because the failure this design is for is the session
that *does not reach its end* — killed, out of context, crashed. Saving at the end protects
against exactly the cases that were going to be fine anyway.
"""

from . import session as sess
from . import state as st


class HarnessError(Exception):
    """Raised when the harness is asked to declare something it cannot support."""


class Harness:
    def __init__(
        self,
        features,
        verifier,
        progress_path,
        max_steps=8,
        max_sessions=50,
        max_attempts=3,
    ):
        self.progress_path = progress_path
        self.verifier = verifier
        self.max_steps = max_steps
        self.max_sessions = max_sessions
        # Per-feature retry cap. Without it, `run` re-verifies a feature whose check will
        # never pass until the session budget is gone — burning every remaining session on
        # the one thing that cannot succeed, and reporting the symptom (budget exhausted)
        # rather than the cause (this check keeps failing).
        #
        # This is the "no-progress" half of the bounded-loop rule the architecture docs state:
        # steps, wall-clock, tokens, *and* no-progress. The first three were already here; a
        # run of the demo is what showed the fourth was missing.
        self.max_attempts = max_attempts
        self.attempts = {f: 0 for f in features}

        existing = st.load(progress_path)
        if existing is None:
            self.progress = st.Progress(features)
            self.resumed = False
            st.save(self.progress, self.progress_path)
        else:
            if existing.features != list(features):
                raise HarnessError(
                    "the feature list changed between sessions: "
                    f"on disk {existing.features}, requested {list(features)}. "
                    "Resolve deliberately rather than silently discarding recorded progress"
                )
            self.progress = existing
            self.resumed = True

    def _save(self):
        st.save(self.progress, self.progress_path)

    def next_feature(self):
        """The next thing to work on, or None.

        Claimed-but-unverified features come first: that is a feature a previous session
        started and did not finish, and picking up new work while one is half-done is how the
        environment degrades across sessions.
        """
        stalled = [
            f
            for f in self.progress.in_state(st.CLAIMED)
            if self.attempts[f] < self.max_attempts
        ]
        if stalled:
            return stalled[0]
        pending = [
            f
            for f in self.progress.in_state(st.PENDING)
            if self.attempts[f] < self.max_attempts
        ]
        return pending[0] if pending else None

    def exhausted(self):
        """Features that hit the retry cap without ever verifying.

        Reported rather than raised. A harness that cannot finish should say which check is
        failing — that is actionable — instead of announcing that it ran out of sessions,
        which is not.
        """
        return [
            f
            for f in self.progress.remaining()
            if self.attempts[f] >= self.max_attempts
        ]

    def run_session(self):
        """One session: claim one feature, verify it, complete it if the verifier agrees.

        Returns the Result, or None when there is nothing left to do. A failed verification
        is not an exception — it is the normal case that leaves the feature CLAIMED for the
        next session to retry.
        """
        feature = self.next_feature()
        if feature is None:
            return None

        self.progress.session += 1
        if self.progress.session > self.max_sessions:
            raise HarnessError(
                f"session budget exhausted ({self.max_sessions}) with "
                f"{len(self.progress.remaining())} feature(s) remaining: "
                f"{self.progress.remaining()}"
            )

        session = sess.Session(self.progress, self.verifier, max_steps=self.max_steps)
        try:
            # A feature left CLAIMED by a previous session is already claimed; re-claiming it
            # would raise, because claim() requires PENDING.
            if self.progress.state(feature) == st.PENDING:
                session.claim(feature)
            else:
                session.claimed = feature
            self._save()

            self.attempts[feature] += 1
            result = session.verify()
            self._save()

            if result.passed:
                session.mark_complete()
                self._save()
            return result
        finally:
            session.close()

    def reset_attempts(self, feature=None):
        """Clear the retry counter, for when the underlying check has been fixed.

        Explicit rather than automatic. A harness that silently resets its own no-progress
        counter does not have one — the counter has to mean something across runs, so
        clearing it is a decision someone makes after changing the thing that was failing.
        """
        if feature is None:
            self.attempts = {f: 0 for f in self.progress.features}
        else:
            if feature not in self.attempts:
                raise HarnessError(f"unknown feature: {feature!r}")
            self.attempts[feature] = 0

    def run(self):
        """Sessions until everything is complete or the budget runs out."""
        results = []
        while not self.progress.is_finished():
            result = self.run_session()
            if result is None:
                break
            results.append(result)
        return results

    def finish(self):
        """Declare the work done — or refuse.

        The refusal is the point of the method. `is_finished()` reads the progress file's
        states, so "done" is a fact about what was verified, and no amount of model confidence
        reaches this decision. Premature completion stops being a behaviour to discourage and
        becomes a transition that does not exist.
        """
        if not self.progress.is_finished():
            remaining = self.progress.remaining()
            message = (
                f"cannot finish: {len(remaining)} feature(s) not complete: {remaining}"
            )
            stuck = self.exhausted()
            if stuck:
                message += f"; verification never passed for {stuck}"
            raise HarnessError(message)
        self._save()
        return True
