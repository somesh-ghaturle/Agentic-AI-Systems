"""Runs the harness end to end, then shows what it refuses to do.

    python3 agent.py

No model, no network, no key. The "agent" is a scripted verifier — see the module docstring
in harness/verify.py for why the interesting invariants are all on the harness side and
therefore testable without one.
"""

import pathlib
import tempfile

from harness import Harness, HarnessError, ScriptedVerifier, state

FEATURES = ["parse-input", "render-output", "persist-results"]


def banner(text):
    print(f"\n{text}\n{'-' * len(text)}")


def main():
    with tempfile.TemporaryDirectory() as workdir:
        progress_path = pathlib.Path(workdir) / "progress.json"

        # 'persist-results' fails its check the first time. That is the interesting path:
        # the run stops short, and the progress file records exactly where.
        verifier = ScriptedVerifier(
            {"parse-input": True, "render-output": True, "persist-results": False}
        )
        harness = Harness(FEATURES, verifier, progress_path, max_sessions=6)

        banner("Sessions")
        for number, result in enumerate(harness.run(), start=1):
            mark = "pass" if result.passed else "FAIL"
            print(f"  session {number}: {result.feature:<16} {mark}")

        banner("Progress file")
        for feature in harness.progress.features:
            print(f"  {feature:<16} {harness.progress.state(feature)}")

        banner("What the harness refuses")
        try:
            harness.finish()
        except HarnessError as exc:
            print(f"  finish() -> HarnessError: {exc}")
        print(f"  stopped after {harness.progress.session} sessions, not "
              f"{harness.max_sessions} — the no-progress bound, not the session budget")

        # The same file, read fresh from disk. A new process would see exactly this — which
        # is the whole claim the atomic write is making.
        reloaded = state.load(progress_path)
        print(f"  reloaded from disk, session={reloaded.session}, "
              f"remaining={reloaded.remaining()}")

        banner("After the failing check is fixed")
        verifier.outcomes["persist-results"] = True
        # Explicit: the no-progress counter is only cleared by someone who changed the thing
        # that was failing. See Harness.reset_attempts.
        harness.reset_attempts("persist-results")
        harness.run()
        for feature in harness.progress.features:
            print(f"  {feature:<16} {harness.progress.state(feature)}")
        print(f"  finish() -> {harness.finish()}")


if __name__ == "__main__":
    main()
