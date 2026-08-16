"""Asserts the harness constrains the agent, not the other way round.

unittest rather than pytest: every other suite in this repository is stdlib unittest, and
pytest is in no requirements file here.

    python3 -m unittest tests.test_harness_agent -v

The example contains no model, which is what makes these tests possible. A harness's
guarantees are properties of the harness — it either refuses a transition or it does not — so
the "agent" is a scripted verifier and every assertion below is deterministic and offline.

The four named failure modes from Anthropic's "Effective harnesses for long-running agents"
each get a class:

    TestPrematureCompletion   finish() refuses while anything is unverified
    TestOverAmbition          one feature per session, enforced not requested
    TestIncompleteTesting     COMPLETE is unreachable without a passing verifier
    TestStateDegradation      the progress file is never left unreadable

A fifth class, TestNoProgressBound, covers a bug found by running the demo rather than by
reading the code: the harness retried a permanently-failing check until the session budget
was gone, then reported the budget rather than the failing check.
"""

import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(
    0, str(pathlib.Path(__file__).resolve().parent.parent / "examples" / "harness-agent")
)

from harness import (
    CLAIMED,
    COMPLETE,
    PENDING,
    VERIFIED,
    AlwaysPasses,
    Harness,
    HarnessError,
    Progress,
    ScriptedVerifier,
    Session,
    SessionError,
    StateError,
    load,
    save,
)

FEATURES = ["alpha", "beta", "gamma"]


class HarnessTestCase(unittest.TestCase):
    """Gives each test its own temp directory and progress path."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = pathlib.Path(self._tmp.name) / "progress.json"

    def harness(self, outcomes=None, **kwargs):
        verifier = ScriptedVerifier(outcomes if outcomes else {}, default=True)
        return Harness(FEATURES, verifier, self.path, **kwargs)


class TestPrematureCompletion(HarnessTestCase):
    """The agent does not get to say it is finished."""

    def test_finish_refuses_on_a_fresh_harness(self):
        h = self.harness()
        with self.assertRaises(HarnessError) as ctx:
            h.finish()
        self.assertIn("not complete", str(ctx.exception))

    def test_finish_refuses_with_one_feature_outstanding(self):
        h = self.harness(outcomes={"alpha": True, "beta": True, "gamma": False})
        h.run()
        self.assertEqual(h.progress.in_state(COMPLETE), ["alpha", "beta"])
        with self.assertRaises(HarnessError) as ctx:
            h.finish()
        self.assertIn("gamma", str(ctx.exception))

    def test_the_error_names_the_check_that_failed_not_the_budget(self):
        """Reporting 'out of sessions' sends someone to the wrong place entirely."""
        h = self.harness(outcomes={"alpha": True, "beta": True, "gamma": False})
        h.run()
        with self.assertRaises(HarnessError) as ctx:
            h.finish()
        self.assertIn("verification never passed", str(ctx.exception))
        self.assertNotIn("session budget", str(ctx.exception))

    def test_finish_succeeds_only_when_every_feature_is_complete(self):
        h = self.harness()
        h.run()
        self.assertTrue(h.progress.is_finished())
        self.assertTrue(h.finish())


class TestOverAmbition(HarnessTestCase):
    """One feature per session, enforced rather than requested."""

    def test_a_second_claim_in_one_session_raises(self):
        progress = Progress(FEATURES)
        session = Session(progress, AlwaysPasses())
        session.claim("alpha")
        with self.assertRaises(SessionError) as ctx:
            session.claim("beta")
        self.assertIn("one feature per session", str(ctx.exception))

    def test_the_second_feature_is_untouched_after_the_refusal(self):
        """A refused claim must not half-apply."""
        progress = Progress(FEATURES)
        session = Session(progress, AlwaysPasses())
        session.claim("alpha")
        with self.assertRaises(SessionError):
            session.claim("beta")
        self.assertEqual(progress.state("beta"), PENDING)

    def test_the_step_budget_is_a_bound_not_a_suggestion(self):
        progress = Progress(FEATURES)
        session = Session(progress, AlwaysPasses(), max_steps=1)
        session.claim("alpha")
        with self.assertRaises(SessionError) as ctx:
            session.verify()
        self.assertIn("step budget exhausted", str(ctx.exception))

    def test_a_closed_session_does_no_further_work(self):
        progress = Progress(FEATURES)
        session = Session(progress, AlwaysPasses())
        session.close()
        with self.assertRaises(SessionError):
            session.claim("alpha")

    def test_each_run_session_uses_a_fresh_session(self):
        h = self.harness()
        h.run_session()
        h.run_session()
        self.assertEqual(h.progress.in_state(COMPLETE), ["alpha", "beta"])


class TestIncompleteTesting(HarnessTestCase):
    """COMPLETE is unreachable without a verifier that passed."""

    def test_a_failing_verifier_leaves_the_feature_claimed(self):
        h = self.harness(outcomes={"alpha": False})
        h.run_session()
        self.assertEqual(h.progress.state("alpha"), CLAIMED)

    def test_mark_complete_from_claimed_raises(self):
        """The direct route past verification, closed at the state machine."""
        progress = Progress(FEATURES)
        session = Session(progress, AlwaysPasses())
        session.claim("alpha")
        with self.assertRaises(StateError) as ctx:
            session.mark_complete()
        self.assertIn("only legal next state", str(ctx.exception))

    def test_states_cannot_be_skipped(self):
        progress = Progress(FEATURES)
        with self.assertRaises(StateError):
            progress.advance("alpha", VERIFIED)  # PENDING -> VERIFIED skips CLAIMED
        with self.assertRaises(StateError):
            progress.advance("alpha", COMPLETE)

    def test_states_cannot_move_backwards(self):
        progress = Progress(FEATURES)
        progress.advance("alpha", CLAIMED)
        with self.assertRaises(StateError):
            progress.advance("alpha", PENDING)

    def test_a_feature_with_no_verification_command_fails(self):
        """'No check defined' must not read as 'passed'."""
        from harness import CommandVerifier  # noqa: PLC0415

        verifier = CommandVerifier({})
        result = verifier("alpha")
        self.assertFalse(result.passed)
        self.assertIn("no verification command", result.detail)

    def test_the_verifier_is_consulted_not_the_agent(self):
        verifier = ScriptedVerifier({"alpha": True}, default=False)
        h = Harness(FEATURES, verifier, self.path)
        h.run_session()
        self.assertEqual(verifier.calls, ["alpha"])


class TestStateDegradation(HarnessTestCase):
    """The progress file is never left in a state the next session cannot read."""

    def test_progress_survives_a_round_trip(self):
        h = self.harness()
        h.run_session()
        reloaded = load(self.path)
        self.assertEqual(reloaded.state("alpha"), COMPLETE)
        self.assertEqual(reloaded.session, h.progress.session)

    def test_a_missing_file_is_a_first_session_not_an_error(self):
        self.assertIsNone(load(self.path))

    def test_a_corrupt_file_raises_rather_than_silently_restarting(self):
        self.path.write_text("{ this is not json", encoding="utf-8")
        with self.assertRaises(StateError) as ctx:
            load(self.path)
        self.assertIn("not valid JSON", str(ctx.exception))

    def test_a_failed_write_leaves_the_previous_version_intact(self):
        """The atomicity claim, tested by making serialization blow up mid-write."""
        h = self.harness()
        h.run_session()
        good = self.path.read_text(encoding="utf-8")

        class Unserializable:
            pass

        broken = Progress(FEATURES)
        broken._states["alpha"] = Unserializable()  # json.dump will raise on this
        with self.assertRaises(TypeError):
            save(broken, self.path)

        self.assertEqual(self.path.read_text(encoding="utf-8"), good)
        self.assertEqual(load(self.path).state("alpha"), COMPLETE)

    def test_no_temp_files_are_left_behind_after_a_failed_write(self):
        h = self.harness()
        h.run_session()

        class Unserializable:
            pass

        broken = Progress(FEATURES)
        broken._states["alpha"] = Unserializable()
        with self.assertRaises(TypeError):
            save(broken, self.path)

        leftovers = list(self.path.parent.glob(".progress-*"))
        self.assertEqual(leftovers, [], f"temp files left behind: {leftovers}")

    def test_resuming_picks_up_the_unfinished_feature_first(self):
        h = self.harness(outcomes={"alpha": False})
        h.run_session()
        self.assertEqual(h.progress.state("alpha"), CLAIMED)

        resumed = Harness(FEATURES, ScriptedVerifier({}, default=True), self.path)
        self.assertTrue(resumed.resumed)
        self.assertEqual(resumed.next_feature(), "alpha")

    def test_a_changed_feature_list_is_refused_rather_than_merged(self):
        h = self.harness()
        h.run_session()
        with self.assertRaises(HarnessError) as ctx:
            Harness(["alpha", "beta"], AlwaysPasses(), self.path)
        self.assertIn("feature list changed", str(ctx.exception))

    def test_the_written_file_is_valid_json_with_the_schema_version(self):
        h = self.harness()
        h.run_session()
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(raw["schema"], 1)
        self.assertEqual(sorted(raw["states"]), sorted(FEATURES))


class TestNoProgressBound(HarnessTestCase):
    """Found by running the demo, not by reading the code.

    The harness retried a permanently-failing check until the session budget was exhausted,
    then raised about the budget. Three things were wrong: it wasted every remaining session,
    it reported a symptom rather than a cause, and `run` raised instead of returning the
    partial results it had.
    """

    def test_a_permanently_failing_feature_stops_after_max_attempts(self):
        h = self.harness(outcomes={"gamma": False}, max_attempts=3)
        h.run()
        self.assertEqual(h.attempts["gamma"], 3)

    def test_run_returns_partial_results_rather_than_raising(self):
        h = self.harness(outcomes={"gamma": False}, max_attempts=2)
        results = h.run()  # must not raise
        self.assertTrue(any(r.passed for r in results))
        self.assertTrue(any(not r.passed for r in results))

    def test_the_session_budget_is_not_consumed_by_one_broken_check(self):
        h = self.harness(outcomes={"gamma": False}, max_attempts=2, max_sessions=50)
        h.run()
        self.assertLess(h.progress.session, 10)

    def test_exhausted_names_the_stuck_feature(self):
        h = self.harness(outcomes={"gamma": False}, max_attempts=1)
        h.run()
        self.assertEqual(h.exhausted(), ["gamma"])

    def test_resetting_attempts_lets_a_fixed_check_run_again(self):
        verifier = ScriptedVerifier({"gamma": False}, default=True)
        h = Harness(FEATURES, verifier, self.path, max_attempts=2)
        h.run()
        self.assertFalse(h.progress.is_finished())

        verifier.outcomes["gamma"] = True
        h.reset_attempts("gamma")
        h.run()
        self.assertTrue(h.progress.is_finished())

    def test_resetting_is_explicit_not_automatic(self):
        """A second run without a reset must not quietly retry."""
        h = self.harness(outcomes={"gamma": False}, max_attempts=1)
        h.run()
        before = h.progress.session
        h.run()
        self.assertEqual(h.progress.session, before)

    def test_reset_attempts_rejects_an_unknown_feature(self):
        h = self.harness()
        with self.assertRaises(HarnessError):
            h.reset_attempts("not-a-feature")


class TestConstruction(HarnessTestCase):
    """The cheap guards that keep the rest of the suite meaningful."""

    def test_an_empty_feature_list_is_refused(self):
        with self.assertRaises(StateError):
            Progress([])

    def test_duplicate_features_are_refused(self):
        with self.assertRaises(StateError):
            Progress(["alpha", "alpha"])

    def test_states_for_unknown_features_are_refused(self):
        with self.assertRaises(StateError):
            Progress(["alpha"], states={"alpha": PENDING, "ghost": PENDING})

    def test_an_unknown_feature_raises_on_read(self):
        with self.assertRaises(StateError):
            Progress(FEATURES).state("nope")

    def test_a_zero_step_session_is_refused(self):
        with self.assertRaises(SessionError):
            Session(Progress(FEATURES), AlwaysPasses(), max_steps=0)

    def test_a_wrong_schema_version_is_refused(self):
        self.path.write_text(
            json.dumps({"schema": 99, "features": FEATURES, "states": {}}),
            encoding="utf-8",
        )
        with self.assertRaises(StateError) as ctx:
            load(self.path)
        self.assertIn("schema", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
