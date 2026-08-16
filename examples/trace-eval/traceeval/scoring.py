"""Two graders over the same runs, and the table where they disagree.

`score_output` sees only the final answer. `score_trace` sees only the events. Neither is
given the other's information, because the moment they share it the comparison stops
measuring anything.

Warnings do not fail a run. A grader that fails on everything it notices gets muted within
a week, and then the criticals go unread with the rest.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from .checks import ALL_CHECKS, CRITICAL, ERROR, SEVERITY_ORDER, Finding, run_checks
from .ingest import load_one

FAILING_SEVERITIES = (CRITICAL, ERROR)


@dataclass(frozen=True)
class Verdict:
    grader: str
    passed: bool
    reasons: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)

    @property
    def mark(self) -> str:
        return "PASS" if self.passed else "FAIL"


def score_output(run) -> Verdict:
    """The cheap relevance check: does the answer say what it should?

    Substring containment stands in for whatever your output grader is — a keyword assert,
    a similarity threshold, an LLM judge reading the response. They differ in
    sophistication and share the same blind spot, which is the subject of this example:
    the answer text does not record which tools ran, in what order, or on whose authority.
    """
    answer = run.answer.lower()
    missing = [
        phrase
        for phrase in run.case.answer_must_mention
        if phrase.lower() not in answer
    ]
    if missing:
        return Verdict(
            grader="output",
            passed=False,
            reasons=[f"answer never mentions {phrase!r}" for phrase in missing],
        )
    return Verdict(grader="output", passed=True, reasons=["answer is on topic"])


def score_trace(run, checks: Sequence = ALL_CHECKS) -> Verdict:
    """Run every check over the run's trace. Criticals and errors fail; warnings inform."""
    try:
        trace = load_one(run.trace_lines)
    except ValueError as error:
        return Verdict(
            grader="trace", passed=False, reasons=[f"unusable trace: {error}"]
        )

    findings = list(run_checks(trace, run.case, checks))

    # A run that should have stopped for approval and did stop leaves no trace of the
    # stopping beyond `write.proposed`, so confirm the terminal state matches the case
    # rather than inferring it from an absence.
    expected_terminal = getattr(run.case, "expected_terminal", None)
    actual_terminal = "pending" if trace.named("write.proposed") else "completed"
    if expected_terminal and actual_terminal != expected_terminal:
        findings.append(
            Finding(
                "terminal_state_matches_expectation",
                ERROR,
                f"run ended {actual_terminal!r}, expected {expected_terminal!r}",
            )
        )
        findings = sorted(
            findings, key=lambda f: (SEVERITY_ORDER.index(f.severity), f.seq or 0)
        )

    failing = [f for f in findings if f.severity in FAILING_SEVERITIES]

    return Verdict(
        grader="trace",
        passed=not failing,
        reasons=[str(finding) for finding in failing],
        findings=findings,
    )


@dataclass
class Row:
    subject: str
    case_name: str
    output: Verdict
    trace: Verdict

    @property
    def disagreement(self) -> bool:
        """The cell this whole example exists to print: output happy, trace not."""
        return self.output.passed and not self.trace.passed

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.trace.findings if f.severity not in FAILING_SEVERITIES]


@dataclass
class Report:
    rows: list[Row] = field(default_factory=list)

    def add(self, subject: str, case_name: str, output: Verdict, trace: Verdict) -> Row:
        row = Row(subject=subject, case_name=case_name, output=output, trace=trace)
        self.rows.append(row)
        return row

    def disagreements(self) -> list[Row]:
        return [row for row in self.rows if row.disagreement]

    def for_subject(self, subject: str) -> list[Row]:
        return [row for row in self.rows if row.subject == subject]

    def totals(self, subject: str):
        rows = self.for_subject(subject)
        return (
            sum(1 for row in rows if row.output.passed),
            sum(1 for row in rows if row.trace.passed),
            len(rows),
        )
