"""Locks in the approval-gate fuzzer: the sound gate holds, and every broken gate is found.

    python3 -m unittest tests.test_approval_gate_fuzzing -v

No dependencies; these run in the fast `examples` CI job.

The earlier suite asserted that a phrase detector recognised the phrases it was written from.
These assert something that can be false: that no generated attack gets an unapproved write
past the gate, and that the fuzzer is sharp enough to catch gates that are wrong.
"""

import contextlib
import io
import pathlib
import sys
import unittest
from unittest import mock

sys.path.insert(
    0,
    str(pathlib.Path(__file__).resolve().parent.parent / "examples" / "approval-gate-fuzzing"),
)

import fuzz as af


def sound():
    return af.Gate(af.Approvals())


class TestTheSoundGateHolds(unittest.TestCase):
    def test_no_case_gets_an_unapproved_write_through(self):
        self.assertIsNone(af.first_failure(sound))

    def test_an_approved_write_still_runs(self):
        self.assertTrue(af.approved_write_runs(sound))

    def test_a_replayed_token_runs_once(self):
        case = next(c for c in af.cases() if c.name.startswith("replayed-token"))
        gate = sound()
        for call in case.calls(gate.approvals, "note"):
            with contextlib.suppress(af.Refused):
                gate.execute(call)
        self.assertEqual(gate.effects, [af.TARGET])

    def test_a_gate_that_refuses_everything_is_not_a_pass(self):
        class RefusesEverything(af.Gate):
            def execute(self, call):
                raise af.Refused("no")

        make = lambda: RefusesEverything(af.Approvals())  # noqa: E731
        self.assertIsNone(af.first_failure(make))
        self.assertFalse(af.approved_write_runs(make))


EXPECTED = {
    "trusts-the-note": "no-token",
    "checks-tool-not-arguments": "token-for-other-arguments",
    "reusable-token": "replayed-token",
    "denylist-of-writes": "unregistered-write",
}


class TestEveryBrokenGateIsFound(unittest.TestCase):
    def test_each_is_found_by_the_forgery_that_targets_its_flaw(self):
        self.assertEqual(set(af.BROKEN), set(EXPECTED))
        for name, make_gate in af.BROKEN.items():
            found = af.first_failure(make_gate)
            self.assertIsNotNone(found, name)
            self.assertTrue(found.name.startswith(EXPECTED[name]), (name, found.name))

    def test_main_fails_when_the_fuzzer_loses_coverage(self):
        patch = mock.patch.dict(af.BROKEN, {"actually-sound": sound})
        with patch, contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(af.main(), 1)
        self.assertIn("NOT FOUND", out.getvalue())

    def test_main_passes_on_the_shipped_gates(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(af.main(), 0)


class TestThePromptIsNotTheBoundary(unittest.TestCase):
    def test_the_old_filter_misses_most_of_the_generated_prompts(self):
        flagged = [p for p in af.prompts() if af.old_filter_flags(p)]
        self.assertEqual(len(af.prompts()), 48)
        self.assertEqual(len(flagged), 8)

    def test_every_obfuscation_changes_the_text(self):
        phrase = af.PHRASINGS[0]
        for name, obfuscate in af.OBFUSCATIONS.items():
            if name != "plain":
                self.assertNotIn(phrase, obfuscate(phrase), name)


if __name__ == "__main__":
    unittest.main()
