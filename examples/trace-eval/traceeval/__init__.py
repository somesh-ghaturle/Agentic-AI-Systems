"""Trace-level evaluation — scoring the path a run took, not only the answer it gave."""

from .checks import ALL_CHECKS, CRITICAL, ERROR, WARNING, Finding, run_checks
from .dataset import CASES, Case
from .ingest import Event, Trace, load, load_one, parse_line
from .scoring import Report, Row, Verdict, score_output, score_trace

__all__ = [
    "ALL_CHECKS",
    "CASES",
    "CRITICAL",
    "ERROR",
    "WARNING",
    "Case",
    "Event",
    "Finding",
    "Report",
    "Row",
    "Trace",
    "Verdict",
    "load",
    "load_one",
    "parse_line",
    "run_checks",
    "score_output",
    "score_trace",
]
