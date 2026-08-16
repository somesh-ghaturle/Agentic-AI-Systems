"""The progress file: the only thing that survives a context window.

A long-running agent does not get to keep its working memory. The session ends, the context
is gone, and the next session starts from whatever was written down. That makes this file the
agent's entire continuity, and it makes a corrupt progress file worse than no progress file —
an agent that cannot read its own state does not stop, it starts over.

So the invariant here is narrow and absolute: **the file on disk is always valid JSON matching
the schema, or it does not exist.** There is no third state. Every write goes to a temporary
file in the same directory and is then renamed over the target, because `os.replace` is atomic
on POSIX and on Windows. A process killed mid-write leaves the previous version intact.

Writing JSON directly to the destination with `open(path, "w")` would truncate first and write
second, which is a window — small, but exactly the window a killed session lands in.
"""

import json
import os
import pathlib
import tempfile

# Feature states. The order matters: a feature moves forward through these and never back,
# which is what `advance` enforces.
PENDING = "pending"
CLAIMED = "claimed"
VERIFIED = "verified"
COMPLETE = "complete"

ORDER = [PENDING, CLAIMED, VERIFIED, COMPLETE]

SCHEMA_VERSION = 1


class StateError(Exception):
    """Raised when a transition would violate the progress file's invariants."""


class Progress:
    """The feature list and its states, plus the session counter.

    Deliberately not a dataclass: every mutation has a rule attached, and public attributes
    would let a caller move a feature to `complete` by assignment, which is the exact thing
    this class exists to prevent.
    """

    def __init__(self, features, states=None, session=0):
        if not features:
            raise StateError("a harness with no features has nothing to verify")
        if len(set(features)) != len(features):
            raise StateError(f"duplicate feature names: {features}")
        self._features = list(features)
        self._states = dict(states) if states else dict.fromkeys(features, PENDING)
        self.session = session

        unknown = set(self._states) - set(self._features)
        if unknown:
            raise StateError(f"states for unknown features: {sorted(unknown)}")

    # -- reading ------------------------------------------------------------------

    @property
    def features(self):
        return list(self._features)

    def state(self, feature):
        if feature not in self._states:
            raise StateError(f"unknown feature: {feature!r}")
        return self._states[feature]

    def in_state(self, state):
        return [f for f in self._features if self._states[f] == state]

    def is_finished(self):
        """True only when every feature is COMPLETE.

        This is the predicate `finish()` consults, and the reason premature completion is
        structurally impossible rather than merely discouraged.
        """
        return all(self._states[f] == COMPLETE for f in self._features)

    def remaining(self):
        return [f for f in self._features if self._states[f] != COMPLETE]

    # -- writing ------------------------------------------------------------------

    def advance(self, feature, to):
        """Move a feature exactly one step forward.

        One step, forward only. Skipping is what "marked complete without testing" looks like
        in code — `advance(f, COMPLETE)` from CLAIMED would be precisely that — so the step
        size is checked rather than the destination alone.
        """
        if to not in ORDER:
            raise StateError(f"not a state: {to!r}")
        current = self.state(feature)
        expected = ORDER[ORDER.index(current) + 1] if current != COMPLETE else None
        if to != expected:
            raise StateError(
                f"{feature!r} is {current!r}; the only legal next state is {expected!r}, "
                f"not {to!r}"
            )
        self._states[feature] = to

    # -- persistence --------------------------------------------------------------

    def to_dict(self):
        return {
            "schema": SCHEMA_VERSION,
            "session": self.session,
            "features": self._features,
            "states": self._states,
        }

    @classmethod
    def from_dict(cls, raw):
        if raw.get("schema") != SCHEMA_VERSION:
            raise StateError(
                f"progress file schema {raw.get('schema')!r}, expected {SCHEMA_VERSION}"
            )
        return cls(
            features=raw["features"],
            states=raw["states"],
            session=raw.get("session", 0),
        )


def save(progress, path):
    """Write the progress file atomically.

    Temp file in the *same directory* as the target, then `os.replace`. Same directory because
    rename is only atomic within a filesystem, and /tmp is frequently a different one.
    """
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".progress-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(progress.to_dict(), handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except BaseException:
        # Leave no partial temp files behind on failure, but never touch the destination —
        # the whole point is that the previous good version stays readable.
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def load(path):
    """Read the progress file, or return None if it has never been written.

    A missing file is a legitimate first-session state and not an error. A file that exists
    but does not parse *is* an error, and is raised rather than swallowed: silently starting
    over is how an agent redoes finished work.
    """
    path = pathlib.Path(path)
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise StateError(f"progress file at {path} is not valid JSON: {exc}") from exc
    return Progress.from_dict(raw)
