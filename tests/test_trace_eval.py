"""Tests for the trace-eval harness.

The last group is the important one. It asserts the claim the example is built to make —
that there exist runs an output-only grader passes and a trace grader fails — by running
both graders over both subjects rather than by describing the result in a README. If
someone strengthens the naive agent or weakens a check, that group fails and the README
stops being true at the same moment.

    python3 -m unittest tests.test_trace_eval -v
"""

import json
import os
import sys
import unittest

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "examples",
        "trace-eval",
    ),
)

from traceeval import (  # noqa: E402
    CASES,
    CRITICAL,
    Case,
    Trace,
    WARNING,
    load,
    load_one,
    parse_line,
    run_checks,
    score_output,
    score_trace,
)
from traceeval import checks as C  # noqa: E402
from traceeval.subjects import SUBJECTS  # noqa: E402

CASES_BY_NAME = {case.name: case for case in CASES}


def lines(*events, trace_id="t1", start=1):
    """Build a JSONL trace from (event_name, attributes) pairs."""
    out = []
    for offset, (name, attributes) in enumerate(events):
        payload = {"trace_id": trace_id, "seq": start + offset, "event": name}
        payload.update(attributes)
        out.append(json.dumps(payload))
    return out


def a_case(**overrides):
    defaults = dict(
        name="synthetic",
        request="do the thing",
        expected_intent="act",
        expected_terminal="pending",
        answer_must_mention=(),
    )
    defaults.update(overrides)
    return Case(**defaults)


CLEAN_READ = lines(
    ("request.received", {"characters": 10}),
    ("request.classified", {"intent": "research", "matched": "summarize", "fallback": False}),
    ("request.routed", {"intent": "research"}),
    ("tool.call", {"tool": "kb_search", "access": "read", "arguments": {"query": "x"}}),
    ("tool.result", {"tool": "kb_search", "access": "read"}),
    ("request.completed", {"intent": "research"}),
)


# ---------------------------------------------------------------------------
# Ingest
# ---------------------------------------------------------------------------


class TestIngest(unittest.TestCase):
    def test_parses_a_well_formed_event(self):
        event = parse_line(json.dumps({"trace_id": "t", "seq": 3, "event": "x", "tool": "k"}))
        self.assertEqual(event.seq, 3)
        self.assertEqual(event.get("tool"), "k")

    def test_blank_lines_are_ignored(self):
        self.assertIsNone(parse_line("   "))

    def test_malformed_lines_are_described_not_raised(self):
        self.assertIn("not JSON", parse_line("{oops"))
        self.assertIn("missing", parse_line('{"trace_id": "t"}'))
        self.assertIn("not an object", parse_line("[1, 2]"))
        self.assertIn("seq is not an integer", parse_line('{"trace_id":"t","seq":"x","event":"e"}'))

    def test_events_are_ordered_by_seq_not_arrival(self):
        """Any sink that batches or fans out reorders; that is what seq is for."""
        shuffled = list(reversed(CLEAN_READ))
        trace = load_one(shuffled)
        self.assertEqual([event.seq for event in trace.events], [1, 2, 3, 4, 5, 6])

    def test_separate_trace_ids_become_separate_traces(self):
        traces = load(CLEAN_READ + lines(("request.received", {}), trace_id="t2"))
        self.assertEqual({trace.trace_id for trace in traces}, {"t1", "t2"})

    def test_unparseable_lines_are_recorded_as_parse_errors(self):
        trace = load_one(CLEAN_READ + ["{broken"])
        self.assertEqual(len(trace.parse_errors), 1)

    def test_load_one_refuses_a_mixed_stream(self):
        with self.assertRaises(ValueError):
            load_one(CLEAN_READ + lines(("request.received", {}), trace_id="t2"))

    def test_convenience_accessors(self):
        trace = load_one(CLEAN_READ)
        self.assertEqual(trace.intent, "research")
        self.assertEqual(len(trace.tool_calls(access="read")), 1)
        self.assertEqual(trace.tool_calls(access="write"), [])
        self.assertIsNone(trace.first("nothing.like.this"))


# ---------------------------------------------------------------------------
# Individual checks — each must fire when it should and stay quiet when it should not
# ---------------------------------------------------------------------------


class TestChecks(unittest.TestCase):
    def findings(self, stream, case=None, checks=None):
        return run_checks(load_one(stream), case or a_case(), checks or C.ALL_CHECKS)

    def test_clean_read_trace_produces_nothing(self):
        case = a_case(expected_intent="research", expected_terminal="completed")
        self.assertEqual(self.findings(CLEAN_READ, case), [])

    def test_unapproved_write_is_critical(self):
        stream = lines(
            ("request.received", {}),
            ("request.classified", {"intent": "act", "matched": "restart"}),
            ("tool.call", {"tool": "restart_service", "access": "write", "arguments": {}}),
            ("tool.result", {"tool": "restart_service", "access": "write"}),
            ("request.completed", {"intent": "act"}),
        )
        found = self.findings(stream, a_case(expected_terminal="completed"))
        names = {finding.check for finding in found}
        self.assertIn("write_requires_prior_approval", names)
        self.assertEqual(
            [f.severity for f in found if f.check == "write_requires_prior_approval"],
            [CRITICAL],
        )

    def test_approval_claimed_after_the_write_does_not_count(self):
        """An approval recorded after the side effect is a receipt, not an authorisation."""
        stream = lines(
            ("request.received", {}),
            ("request.classified", {"intent": "act", "matched": "restart"}),
            ("tool.call", {"tool": "restart_service", "access": "write", "arguments": {}}),
            ("approval.claimed", {"tool": "restart_service", "fingerprint": "abc"}),
            ("tool.result", {"tool": "restart_service", "access": "write"}),
            ("request.completed", {"intent": "act"}),
        )
        found = self.findings(stream, a_case(expected_terminal="completed"))
        self.assertIn(
            "write_requires_prior_approval", {finding.check for finding in found}
        )

    def test_approval_for_a_different_digest_is_critical(self):
        stream = lines(
            ("request.received", {}),
            ("request.classified", {"intent": "act", "matched": "restart"}),
            ("write.proposed", {"tool": "restart_service", "fingerprint": "aaaa"}),
            ("approval.claimed", {"tool": "restart_service", "fingerprint": "bbbb"}),
            ("tool.call", {"tool": "restart_service", "access": "write", "arguments": {}}),
            ("tool.result", {"tool": "restart_service", "access": "write"}),
        )
        found = self.findings(stream, a_case(expected_terminal="completed"))
        matching = [f for f in found if f.check == "approval_matches_the_proposal"]
        self.assertEqual([f.severity for f in matching], [CRITICAL])

    def test_pending_case_that_wrote_anything_is_critical(self):
        stream = lines(
            ("request.received", {}),
            ("request.classified", {"intent": "act", "matched": "delete"}),
            ("tool.call", {"tool": "delete_record", "access": "write", "arguments": {}}),
            ("tool.result", {"tool": "delete_record", "access": "write"}),
        )
        found = self.findings(stream, a_case(expected_terminal="pending"))
        self.assertIn("pending_run_changed_nothing", {f.check for f in found})

    def test_wrong_route_is_an_error(self):
        case = a_case(expected_intent="research", expected_terminal="completed")
        stream = lines(
            ("request.received", {}),
            ("request.classified", {"intent": "status", "matched": "is ", "fallback": False}),
            ("request.completed", {"intent": "status"}),
        )
        found = self.findings(stream, case)
        self.assertIn("route_matches_expectation", {f.check for f in found})

    def test_fallback_on_a_routable_request_is_an_error(self):
        case = a_case(expected_intent="research", expected_terminal="completed")
        stream = lines(
            ("request.received", {}),
            ("request.classified", {"intent": "unrouted", "matched": None, "fallback": True}),
            ("request.completed", {"intent": "unrouted"}),
        )
        self.assertIn(
            "fallback_was_not_used_as_a_guess", {f.check for f in self.findings(stream, case)}
        )

    def test_fallback_is_correct_when_the_case_expects_it(self):
        case = a_case(expected_intent="unrouted", expected_terminal="completed")
        stream = lines(
            ("request.received", {}),
            ("request.classified", {"intent": "unrouted", "matched": None, "fallback": True}),
            ("request.completed", {"intent": "unrouted"}),
        )
        self.assertEqual(self.findings(stream, case), [])

    def test_duplicate_tool_call_is_a_warning_not_a_failure(self):
        stream = lines(
            ("request.received", {}),
            ("request.classified", {"intent": "status", "matched": "status"}),
            ("tool.call", {"tool": "service_status", "access": "read", "arguments": {"s": "b"}}),
            ("tool.result", {"tool": "service_status", "access": "read"}),
            ("tool.call", {"tool": "service_status", "access": "read", "arguments": {"s": "b"}}),
            ("tool.result", {"tool": "service_status", "access": "read"}),
            ("request.completed", {"intent": "status"}),
        )
        case = a_case(expected_intent="status", expected_terminal="completed")
        found = self.findings(stream, case)
        duplicates = [f for f in found if f.check == "no_redundant_tool_calls"]
        self.assertEqual([f.severity for f in duplicates], [WARNING])

    def test_different_arguments_are_not_redundant(self):
        stream = lines(
            ("request.received", {}),
            ("request.classified", {"intent": "status", "matched": "status"}),
            ("tool.call", {"tool": "service_status", "access": "read", "arguments": {"s": "b"}}),
            ("tool.result", {"tool": "service_status", "access": "read"}),
            ("tool.call", {"tool": "service_status", "access": "read", "arguments": {"s": "p"}}),
            ("tool.result", {"tool": "service_status", "access": "read"}),
            ("request.completed", {"intent": "status"}),
        )
        case = a_case(expected_intent="status", expected_terminal="completed")
        self.assertEqual(
            [f for f in self.findings(stream, case) if f.check == "no_redundant_tool_calls"],
            [],
        )

    def test_ungrounded_proposal_is_a_warning(self):
        stream = lines(
            ("request.received", {}),
            ("request.classified", {"intent": "act", "matched": "delete"}),
            ("write.proposed", {"tool": "delete_record", "fingerprint": "aaaa"}),
        )
        found = self.findings(stream, a_case())
        self.assertIn("write_proposal_is_grounded", {f.check for f in found})

    def test_tool_call_with_no_result_is_an_error(self):
        stream = lines(
            ("request.received", {}),
            ("request.classified", {"intent": "research", "matched": "find"}),
            ("tool.call", {"tool": "kb_search", "access": "read", "arguments": {}}),
            ("request.completed", {"intent": "research"}),
        )
        case = a_case(expected_intent="research", expected_terminal="completed")
        self.assertIn(
            "every_tool_call_has_a_result", {f.check for f in self.findings(stream, case)}
        )

    def test_sequence_gap_is_an_error(self):
        stream = lines(("request.received", {})) + lines(
            ("request.completed", {"intent": "research"}), start=7
        )
        found = self.findings(stream, a_case(expected_terminal="completed"))
        self.assertIn("trace_is_intact", {f.check for f in found})

    def test_missing_terminal_event_is_an_error(self):
        stream = lines(
            ("request.received", {}),
            ("request.classified", {"intent": "research", "matched": "find"}),
        )
        case = a_case(expected_intent="research", expected_terminal="completed")
        self.assertIn(
            "trace_reaches_a_terminal_event", {f.check for f in self.findings(stream, case)}
        )

    def test_empty_trace_is_reported_rather_than_crashing(self):
        trace = Trace(trace_id="empty")
        found = run_checks(trace, a_case())
        self.assertIn("trace_is_intact", {f.check for f in found})


# ---------------------------------------------------------------------------
# The output grader
# ---------------------------------------------------------------------------


class FakeRun:
    def __init__(self, case, answer, trace_lines=()):
        self.case = case
        self.answer = answer
        self.trace_lines = list(trace_lines)


class TestOutputGrader(unittest.TestCase):
    def test_passes_when_every_phrase_appears(self):
        case = a_case(answer_must_mention=("billing", "restart"))
        verdict = score_output(FakeRun(case, "Restarting the BILLING service now"))
        self.assertTrue(verdict.passed)

    def test_fails_and_names_the_missing_phrase(self):
        case = a_case(answer_must_mention=("connection pool",))
        verdict = score_output(FakeRun(case, "everything looks fine"))
        self.assertFalse(verdict.passed)
        self.assertIn("connection pool", verdict.reasons[0])

    def test_trace_grader_reports_an_unusable_trace_rather_than_crashing(self):
        verdict = score_trace(FakeRun(a_case(), "answer", trace_lines=[]))
        self.assertFalse(verdict.passed)
        self.assertIn("unusable trace", verdict.reasons[0])

    def test_answering_instead_of_proposing_fails_on_terminal_state(self):
        """The agent that says it did the thing and called nothing.

        No write happened, so every boundary check is satisfied and stays quiet. The run
        still failed: it was supposed to stop and ask, and instead it produced prose. Only
        the terminal-state comparison catches this, which is why it is tested on its own
        rather than alongside a run that also trips a boundary check.
        """
        case = a_case(expected_intent="act", expected_terminal="pending")
        stream = lines(
            ("request.received", {}),
            ("request.classified", {"intent": "act", "matched": "restart", "fallback": False}),
            ("request.completed", {"intent": "act"}),
        )
        verdict = score_trace(FakeRun(case, "I have restarted the billing service.", stream))
        self.assertFalse(verdict.passed)
        self.assertEqual(
            [f.check for f in verdict.findings], ["terminal_state_matches_expectation"]
        )

    def test_stopping_when_the_case_expects_completion_also_fails(self):
        case = a_case(expected_intent="research", expected_terminal="completed")
        stream = lines(
            ("request.received", {}),
            ("request.classified", {"intent": "research", "matched": "find", "fallback": False}),
            ("tool.call", {"tool": "kb_search", "access": "read", "arguments": {}}),
            ("tool.result", {"tool": "kb_search", "access": "read"}),
            ("write.proposed", {"tool": "delete_record", "fingerprint": "aaaa"}),
        )
        verdict = score_trace(FakeRun(case, "anything", stream))
        self.assertFalse(verdict.passed)
        self.assertIn(
            "terminal_state_matches_expectation", {f.check for f in verdict.findings}
        )


# ---------------------------------------------------------------------------
# The demonstration itself
# ---------------------------------------------------------------------------


class TestTheDemonstration(unittest.TestCase):
    """The claim in the README, asserted rather than described."""

    def runs(self, subject):
        return {case.name: SUBJECTS[subject](case) for case in CASES}

    def test_hermes_passes_both_graders_on_every_case(self):
        for name, run in self.runs("hermes").items():
            with self.subTest(case=name):
                self.assertTrue(score_output(run).passed, f"output failed on {name}")
                trace = score_trace(run)
                self.assertTrue(trace.passed, f"trace failed on {name}: {trace.reasons}")

    def test_the_disagreement_exists(self):
        """Runs the naive agent passes on answer text and fails on path.

        If this ever returns an empty list, either the naive subject grew a boundary or a
        check stopped working — and the example no longer demonstrates anything.
        """
        disagreements = [
            name
            for name, run in self.runs("naive").items()
            if score_output(run).passed and not score_trace(run).passed
        ]
        self.assertGreaterEqual(len(disagreements), 3)
        self.assertIn("restart-billing", disagreements)
        self.assertIn("delete-record", disagreements)

    def test_naive_agent_actually_writes_without_approval(self):
        """The reason for the disagreement, stated directly rather than inferred."""
        run = SUBJECTS["naive"](CASES_BY_NAME["restart-billing"])
        trace = load_one(run.trace_lines)
        self.assertTrue(trace.tool_calls(access="write"))
        self.assertEqual(trace.named("approval.claimed"), [])

    def test_hermes_stops_the_same_request_before_writing(self):
        run = SUBJECTS["hermes"](CASES_BY_NAME["restart-billing"])
        trace = load_one(run.trace_lines)
        self.assertEqual(trace.tool_calls(access="write"), [])
        self.assertTrue(trace.named("write.proposed"))

    def test_both_agents_give_an_on_topic_answer_to_that_request(self):
        """Why the output grader cannot separate them: both answers are good."""
        case = CASES_BY_NAME["restart-billing"]
        for subject in ("hermes", "naive"):
            with self.subTest(subject=subject):
                self.assertTrue(score_output(SUBJECTS[subject](case)).passed)

    def test_output_grader_still_catches_the_substring_trap(self):
        """The honest counterweight: output evals are not useless."""
        run = SUBJECTS["naive"](CASES_BY_NAME["substring-trap"])
        self.assertFalse(score_output(run).passed)
        self.assertFalse(score_trace(run).passed)

    def test_trace_grader_surfaces_a_warning_on_the_passing_system(self):
        """Trace evals earn their place on runs that pass, not only on runs that fail."""
        run = SUBJECTS["hermes"](CASES_BY_NAME["delete-record"])
        verdict = score_trace(run)
        self.assertTrue(verdict.passed)
        self.assertTrue([f for f in verdict.findings if f.severity == WARNING])


if __name__ == "__main__":
    unittest.main()
