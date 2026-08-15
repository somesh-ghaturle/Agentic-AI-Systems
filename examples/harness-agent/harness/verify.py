"""Verification: the part the agent does not get to grade.

"Premature completion" and "incomplete testing" are both the same underlying mistake — the
agent is the one deciding whether the agent's work is finished. Anything the model asserts
about its own output is a claim, not evidence, and a harness that accepts the claim has no
verification step at all; it has a politeness ritual.

So a `Verifier` here is a callable the *harness* owns, returning a structured result the
harness reads. The model never touches it. In a real system these are the things that already
tell you the truth — a test command's exit code, a type checker, an end-to-end browser run —
and the shape below is deliberately the shape of "I ran something and it exited non-zero".

`AlwaysPasses` exists for the demo and for tests that are about session mechanics rather than
verification. It is not exported as a default anywhere, because a default verifier that passes
is the failure mode wearing a helpful face.
"""

import collections
import subprocess

Result = collections.namedtuple("Result", "feature passed detail")


class CommandVerifier:
    """Runs a shell command per feature and reads the exit code.

    Exit code, not stdout. Parsing output for the word "passed" is how a verifier starts
    agreeing with a test suite that printed a summary and then crashed.
    """

    def __init__(self, commands, timeout=60):
        self.commands = dict(commands)
        self.timeout = timeout

    def __call__(self, feature):
        command = self.commands.get(feature)
        if command is None:
            # An unverifiable feature fails. The alternative — treating "no check defined" as
            # a pass — means adding a feature and forgetting its test marks it complete.
            return Result(feature, False, "no verification command defined")
        try:
            proc = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired:
            return Result(feature, False, f"timed out after {self.timeout}s")
        detail = f"exit {proc.returncode}"
        if proc.returncode != 0:
            tail = (proc.stderr or proc.stdout or "").strip().splitlines()
            if tail:
                detail += f": {tail[-1]}"
        return Result(feature, proc.returncode == 0, detail)


class AlwaysPasses:
    """For the demo and for tests about session mechanics. Never a default."""

    def __call__(self, feature):
        return Result(feature, True, "stub verifier")


class ScriptedVerifier:
    """Passes or fails per feature from a dict, for testing the harness itself.

    Lets a test say "this feature's check fails" without shelling out, which keeps the suite
    fast and free of subprocess flakiness.
    """

    def __init__(self, outcomes, default=False):
        self.outcomes = dict(outcomes)
        self.default = default
        self.calls = []

    def __call__(self, feature):
        self.calls.append(feature)
        passed = self.outcomes.get(feature, self.default)
        return Result(feature, passed, "scripted")
