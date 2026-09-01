#!/usr/bin/env python3
"""HTTP wrapper around the repository's trace-level evaluation logic."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples" / "trace-eval"))

from traceeval import Case, score_output
from traceeval import score_trace as score_trace_path

app = FastAPI(title="Trace Eval Service")


class TraceRequest(BaseModel):
    trace: list[dict[str, Any] | str] = Field(default_factory=list)
    expected_answer: str | None = None
    grading_criteria: dict[str, Any] | None = None
    expected_intent: str | None = None
    expected_terminal: str = "pending"
    request: str = ""
    case_name: str = "service-scored"

    @property
    def answer_must_mention(self) -> tuple[str, ...]:
        criteria = self.grading_criteria or {}
        if "must_mention" in criteria:
            items = criteria["must_mention"]
            if isinstance(items, str):
                return (items,)
            return tuple(str(item) for item in items)
        if self.expected_answer:
            return tuple(part for part in self.expected_answer.split() if part)
        return ()


class ScoreResponse(BaseModel):
    path_score: float
    answer_score: float
    passed: bool
    discrepancies: list[str]


class _SyntheticRun:
    def __init__(self, request: TraceRequest):
        self.trace_lines = [
            line if isinstance(line, str) else json.dumps(line, sort_keys=True)
            for line in request.trace
        ]
        self.answer = request.expected_answer or ""
        self.case = Case(
            name=request.case_name,
            request=request.request or request.expected_answer or "service score",
            expected_intent=request.expected_intent or "research",
            expected_terminal=request.expected_terminal,
            answer_must_mention=request.answer_must_mention,
        )


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/score", response_model=ScoreResponse)
async def score_trace(request: TraceRequest) -> ScoreResponse:
    run = _SyntheticRun(request)
    path_verdict = score_trace_path(run)
    answer_verdict = score_output(run)
    path_score = 1.0 if path_verdict.passed else 0.0
    answer_score = 1.0 if answer_verdict.passed else 0.0
    discrepancies = path_verdict.reasons + answer_verdict.reasons
    passed = path_score >= 0.8 and answer_score >= 0.8
    return ScoreResponse(
        path_score=path_score,
        answer_score=answer_score,
        passed=passed,
        discrepancies=discrepancies,
    )
