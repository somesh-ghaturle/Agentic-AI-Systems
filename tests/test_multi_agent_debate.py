"""Asserts a debate improves a proposal without ever authorizing one.

unittest rather than pytest: every other suite in this repository is stdlib unittest, and
pytest is in no requirements file here.

    python3 -m unittest tests.test_multi_agent_debate -v

The participants are scripted, which is what makes these tests deterministic and offline. A
debate protocol's guarantees are properties of the protocol — it either records surviving
dissent or it does not — so a model behind the roles would add variance without adding
coverage. Same move as `test_harness_agent` with its verifier and `test_trace_eval` with
its graders.

The classes map to the four things that make a debate worth its cost, plus the one thing it
must never do:

    TestNoAuthorization     a Verdict carries no approval, and cannot be made to
    TestBoundedRounds       running out of budget is not convergence
    TestDissentSurvives     an unanswered objection travels with the proposal
    TestAppendOnlyRecord    history cannot be rewritten once the outcome is known
    TestPanelComposition    clones and self-judging arbiters are refused up front
"""

import dataclasses
import pathlib
import sys
import unittest

sys.path.insert(
    0, str(pathlib.Path(__file__).resolve().parent.parent / "examples" / "multi-agent-debate")
)

from debate import (
    DebateError,
    DegeneratePanel,
    Panel,
    Position,
    Role,
    RoleViolation,
    Transcript,
    TranscriptClosed,
    Turn,
    Verdict,
    run_debate,
)

PROPOSAL = {"action": "process_refund", "arguments": {"amount_cents": 4500}}


class Proposer:
    def __init__(self, name="proposer", concessions=0, proposal=None):
        self.name = name
        self._concessions = concessions
        self._proposal = dict(proposal or PROPOSAL)
        self.revise_calls = 0

    def propose(self, goal):
        return dict(self._proposal, rationale=f"goal: {goal}")

    def revise(self, proposal, transcript):
        self.revise_calls += 1
        if self._concessions <= 0:
            return None
        self._concessions -= 1
        return dict(
            proposal,
            arguments={"amount_cents": 2500},
            rationale="conceded on cost",
        )


class Critic:
    """Supports once `satisfied` returns True; opposes until then."""

    def __init__(self, name, perspective, satisfied=lambda p: True):
        self.name = name
        self.perspective = perspective
        self._satisfied = satisfied

    def critique(self, proposal, transcript, round_number):
        ok = self._satisfied(proposal)
        return Turn(
            round=round_number,
            role=Role.CRITIC,
            speaker=self.name,
            position=Position.SUPPORT if ok else Position.OPPOSE,
            rationale="satisfied" if ok else "amount exceeds the ceiling",
            proposal=dict(proposal),
        )


class Arbiter:
    name = "arbiter"

    def converged(self, proposal, transcript):
        speakers = {t.speaker for t in transcript.turns if t.role is Role.CRITIC}
        return all(transcript.last_position(s) is not Position.OPPOSE for s in speakers)


def cheap(proposal):
    return proposal["arguments"]["amount_cents"] <= 2500


def panel(proposer=None, critics=None, arbiter=None):
    return Panel(
        proposer=proposer or Proposer(),
        critics=critics or (Critic("a", "safety"), Critic("b", "cost")),
        arbiter=arbiter or Arbiter(),
    )


class TestNoAuthorization(unittest.TestCase):
    """The point of the example. A debate is not an approval step."""

    def test_verdict_always_requires_human_approval(self):
        verdict = run_debate(panel(), "refund", max_rounds=3)
        self.assertTrue(verdict.requires_human_approval)

    def test_unanimous_agreement_still_requires_human_approval(self):
        """The dangerous case: everyone agreed, so it feels decided. It is not."""
        verdict = run_debate(panel(), "refund", max_rounds=3)
        self.assertTrue(verdict.unanimous, "expected this panel to agree")
        self.assertTrue(verdict.requires_human_approval)

    def test_requires_human_approval_cannot_be_constructed_false(self):
        """There is no field to set. A flag that can be set is a flag that will be."""
        verdict = Verdict(
            proposal=PROPOSAL, transcript=Transcript(), rounds_used=1, converged=True
        )
        self.assertTrue(verdict.requires_human_approval)
        with self.assertRaises(TypeError):
            Verdict(
                proposal=PROPOSAL,
                transcript=Transcript(),
                rounds_used=1,
                converged=True,
                requires_human_approval=False,
            )

    def test_requires_human_approval_cannot_be_assigned(self):
        verdict = run_debate(panel(), "refund", max_rounds=1)
        with self.assertRaises((AttributeError, TypeError)):
            verdict.requires_human_approval = False

    def test_verdict_has_no_approval_field(self):
        """Guards against someone adding one back under a friendlier name."""
        verdict = run_debate(panel(), "refund", max_rounds=1)
        for banned in ("approved", "approval", "authorized", "decision", "auto_approve"):
            self.assertNotIn(
                banned,
                verdict.__dataclass_fields__,
                f"Verdict grew a {banned!r} field; a debate does not authorize actions",
            )


class TestBoundedRounds(unittest.TestCase):
    """Running out of budget is not agreement, and must not look like it."""

    def test_exhausted_budget_is_not_convergence(self):
        never = Critic("b", "cost", satisfied=lambda p: False)
        verdict = run_debate(
            panel(proposer=Proposer(concessions=99), critics=(Critic("a", "safety"), never)),
            "refund",
            max_rounds=2,
        )
        self.assertFalse(verdict.converged)
        self.assertEqual(2, verdict.rounds_used)
        self.assertFalse(verdict.unanimous)

    def test_debate_terminates_against_an_unsatisfiable_critic(self):
        """No infinite argument, even when nobody will ever be satisfied."""
        never = Critic("b", "cost", satisfied=lambda p: False)
        proposer = Proposer(concessions=10**6)
        verdict = run_debate(
            panel(proposer=proposer, critics=(Critic("a", "safety"), never)),
            "refund",
            max_rounds=3,
        )
        self.assertEqual(3, verdict.rounds_used)
        self.assertLessEqual(proposer.revise_calls, 3)

    def test_early_convergence_does_not_spend_the_budget(self):
        verdict = run_debate(panel(), "refund", max_rounds=10)
        self.assertTrue(verdict.converged)
        self.assertEqual(1, verdict.rounds_used)

    def test_zero_rounds_is_refused(self):
        with self.assertRaises(DebateError):
            run_debate(panel(), "refund", max_rounds=0)

    def test_standing_pat_ends_without_convergence(self):
        """A proposer that declines to move is honest non-agreement, not a retry."""
        proposer = Proposer(concessions=0)
        verdict = run_debate(
            panel(
                proposer=proposer,
                critics=(Critic("a", "safety"), Critic("b", "cost", satisfied=cheap)),
            ),
            "refund",
            max_rounds=5,
        )
        self.assertFalse(verdict.converged)
        self.assertEqual(1, verdict.rounds_used)
        self.assertEqual(1, proposer.revise_calls)


class TestDissentSurvives(unittest.TestCase):
    """An objection that was never answered travels with the proposal."""

    def test_unresolved_objection_is_recorded(self):
        verdict = run_debate(
            panel(
                proposer=Proposer(concessions=0),
                critics=(Critic("a", "safety"), Critic("b", "cost", satisfied=cheap)),
            ),
            "refund",
            max_rounds=3,
        )
        self.assertEqual(1, len(verdict.dissent))
        self.assertEqual("b", verdict.dissent[0].speaker)
        self.assertIn("ceiling", verdict.dissent[0].rationale)

    def test_answered_objection_is_not_dissent(self):
        """A critic satisfied by a revision is not a dissenter."""
        verdict = run_debate(
            panel(
                proposer=Proposer(concessions=1),
                critics=(Critic("a", "safety"), Critic("b", "cost", satisfied=cheap)),
            ),
            "refund",
            max_rounds=3,
        )
        self.assertTrue(verdict.converged)
        self.assertEqual((), verdict.dissent)

    def test_dissent_is_not_dropped_when_the_arbiter_calls_convergence(self):
        """An arbiter may end the debate over a standing objection. It still gets recorded."""

        class EagerArbiter:
            name = "arbiter"

            def converged(self, proposal, transcript):
                return True

        verdict = run_debate(
            panel(
                proposer=Proposer(concessions=0),
                critics=(Critic("a", "safety"), Critic("b", "cost", satisfied=cheap)),
                arbiter=EagerArbiter(),
            ),
            "refund",
            max_rounds=3,
        )
        self.assertTrue(verdict.converged)
        self.assertEqual(1, len(verdict.dissent), "convergence must not erase the objection")
        self.assertFalse(verdict.unanimous)

    def test_rationale_is_required(self):
        """An objection nobody can answer is not a contribution."""
        with self.assertRaises(ValueError):
            Turn(1, Role.CRITIC, "b", Position.OPPOSE, "   ")


class TestAppendOnlyRecord(unittest.TestCase):
    """History cannot be rewritten once the outcome is known."""

    def test_transcript_is_closed_by_the_verdict(self):
        verdict = run_debate(panel(), "refund", max_rounds=1)
        self.assertTrue(verdict.transcript.closed)
        with self.assertRaises(TranscriptClosed):
            verdict.transcript.append(Turn(9, Role.CRITIC, "a", Position.SUPPORT, "late"))

    def test_turns_are_not_the_internal_list(self):
        """Returning the list would allow mutation past every append() guard."""
        transcript = Transcript()
        transcript.append(Turn(1, Role.CRITIC, "a", Position.SUPPORT, "fine"))
        transcript.turns  # noqa: B018 — the point is that this is a copy
        self.assertIsInstance(transcript.turns, tuple)
        self.assertEqual(1, len(transcript))

    def test_a_turn_is_frozen(self):
        turn = Turn(1, Role.CRITIC, "a", Position.OPPOSE, "too expensive")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            turn.position = Position.SUPPORT

    def test_transcript_records_every_participant(self):
        verdict = run_debate(
            panel(
                proposer=Proposer(concessions=1),
                critics=(Critic("a", "safety"), Critic("b", "cost", satisfied=cheap)),
            ),
            "refund",
            max_rounds=3,
        )
        speakers = {t.speaker for t in verdict.transcript.turns}
        self.assertEqual({"proposer", "a", "b"}, speakers)

    def test_each_turn_carries_the_proposal_it_addressed(self):
        """Otherwise 'what were they objecting to' is unanswerable after a revision."""
        verdict = run_debate(
            panel(
                proposer=Proposer(concessions=1),
                critics=(Critic("a", "safety"), Critic("b", "cost", satisfied=cheap)),
            ),
            "refund",
            max_rounds=3,
        )
        objection = next(t for t in verdict.transcript.turns if t.position is Position.OPPOSE)
        self.assertEqual(4500, objection.proposal["arguments"]["amount_cents"])
        self.assertEqual(2500, verdict.proposal["arguments"]["amount_cents"])


class TestPanelComposition(unittest.TestCase):
    """A panel that cannot disagree is worse than no panel: it looks like corroboration."""

    def test_single_critic_is_refused(self):
        with self.assertRaises(DegeneratePanel):
            Panel(proposer=Proposer(), critics=(Critic("a", "safety"),), arbiter=Arbiter())

    def test_clone_critics_are_refused(self):
        with self.assertRaises(DegeneratePanel):
            Panel(
                proposer=Proposer(),
                critics=(Critic("a", "safety"), Critic("b", "safety")),
                arbiter=Arbiter(),
            )

    def test_duplicate_names_are_refused(self):
        """Shared names would merge two participants' turns in by_speaker()."""
        with self.assertRaises(DegeneratePanel):
            Panel(
                proposer=Proposer(),
                critics=(Critic("a", "safety"), Critic("a", "cost")),
                arbiter=Arbiter(),
            )

    def test_arbiter_cannot_also_be_the_proposer(self):
        with self.assertRaises(RoleViolation):
            Panel(
                proposer=Proposer(name="same"),
                critics=(Critic("a", "safety"), Critic("b", "cost")),
                arbiter=type("A", (), {"name": "same", "converged": lambda *_: True})(),
            )

    def test_arbiter_cannot_also_be_a_critic(self):
        with self.assertRaises(RoleViolation):
            Panel(
                proposer=Proposer(),
                critics=(Critic("arbiter", "safety"), Critic("b", "cost")),
                arbiter=Arbiter(),
            )

    def test_arbiter_taking_a_position_is_refused(self):
        p = panel()
        with self.assertRaises(RoleViolation):
            p.check_turn(Turn(1, Role.ARBITER, "arbiter", Position.OPPOSE, "I disagree"))

    def test_critic_issuing_a_proposal_is_refused(self):
        p = panel()
        with self.assertRaises(RoleViolation):
            p.check_turn(Turn(1, Role.CRITIC, "a", Position.PROPOSE, "how about this instead"))


class TestProtocolMisuse(unittest.TestCase):
    def test_proposal_must_name_an_action(self):
        class Bad(Proposer):
            def propose(self, goal):
                return {"rationale": "no action key"}

        with self.assertRaises(DebateError):
            run_debate(panel(proposer=Bad()), "refund", max_rounds=1)

    def test_critic_stamping_the_wrong_round_is_caught(self):
        """An off-by-one here silently reorders last_position, which dissent is built from."""

        class Drifting(Critic):
            def critique(self, proposal, transcript, round_number):
                return Turn(round_number + 5, Role.CRITIC, self.name, Position.SUPPORT, "ok")

        with self.assertRaises(DebateError):
            run_debate(
                panel(critics=(Critic("a", "safety"), Drifting("b", "cost"))),
                "refund",
                max_rounds=1,
            )


if __name__ == "__main__":
    unittest.main()
