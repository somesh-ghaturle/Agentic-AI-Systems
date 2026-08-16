#!/usr/bin/env python3
"""Score two agents on the same cases with two graders, and print where they disagree.

    python3 examples/trace-eval/eval.py                    # both subjects, full report
    python3 examples/trace-eval/eval.py --subject hermes   # one subject
    python3 examples/trace-eval/eval.py --case restart-billing --verbose
    python3 examples/trace-eval/eval.py --subject hermes --strict   # for CI

Nothing to install, no model, no network.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from traceeval import CASES, score_output, score_trace
from traceeval.scoring import Report
from traceeval.subjects import SUBJECTS


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="trace-eval",
        description="Compare output-only scoring against trace-level scoring.",
    )
    parser.add_argument(
        "--subject",
        action="append",
        choices=sorted(SUBJECTS),
        help="subject to evaluate (repeatable; default: all)",
    )
    parser.add_argument("--case", action="append", help="case name (repeatable)")
    parser.add_argument(
        "--verbose", action="store_true", help="print every finding, warnings included"
    )
    parser.add_argument("--json", action="store_true", help="machine-readable report")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 if any selected subject fails trace scoring",
    )
    args = parser.parse_args(argv)

    subjects = args.subject or sorted(SUBJECTS)
    cases = [case for case in CASES if not args.case or case.name in args.case]
    if not cases:
        parser.error(f"no case named {args.case}; have {[c.name for c in CASES]}")

    report = Report()
    for subject in subjects:
        for case in cases:
            run = SUBJECTS[subject](case)
            report.add(subject, case.name, score_output(run), score_trace(run))

    if args.json:
        print(json.dumps(_as_dict(report), indent=2, sort_keys=True))
    else:
        _print_report(report, subjects, args.verbose)

    if args.strict:
        failed = [row for row in report.rows if not row.trace.passed]
        return 1 if failed else 0
    return 0


def _print_report(report: Report, subjects, verbose: bool) -> None:
    for subject in subjects:
        rows = report.for_subject(subject)
        output_passes, trace_passes, total = report.totals(subject)
        print(f"\n{'=' * 78}\n{subject}\n{'=' * 78}")
        print(f"{'case':28} {'output':>8} {'trace':>8}   findings")
        print("-" * 78)
        for row in rows:
            headline = ""
            if not row.trace.passed:
                headline = row.trace.reasons[0]
            elif row.warnings:
                headline = f"{len(row.warnings)} warning(s)"
            print(
                f"{row.case_name:28} {row.output.mark:>8} {row.trace.mark:>8}   "
                f"{_clip(headline)}"
            )
            if verbose:
                for finding in row.trace.findings:
                    print(f"{'':49}{finding}")
        print("-" * 78)
        print(
            f"{'':28} {output_passes:>3}/{total:<4} {trace_passes:>3}/{total:<4}"
            "   passed"
        )

    disagreements = report.disagreements()
    print(f"\n{'=' * 78}\nwhere the two graders disagree\n{'=' * 78}")
    if not disagreements:
        print("None. On these cases the answer text was enough.")
        return

    print(
        f"{len(disagreements)} run(s) an output-only eval scored as PASS and the trace "
        "scored as FAIL.\nThe answer was fine. The path was not:\n"
    )
    for row in disagreements:
        print(f"  {row.subject}/{row.case_name}")
        for reason in row.trace.reasons:
            print(f"      {reason}")


def _as_dict(report: Report) -> dict:
    return {
        "rows": [
            {
                "subject": row.subject,
                "case": row.case_name,
                "output": row.output.mark,
                "trace": row.trace.mark,
                "disagreement": row.disagreement,
                "findings": [str(finding) for finding in row.trace.findings],
            }
            for row in report.rows
        ],
        "disagreements": len(report.disagreements()),
    }


def _clip(text: str, width: int = 44) -> str:
    return text if len(text) <= width else text[: width - 1] + "…"


if __name__ == "__main__":
    sys.exit(main())
