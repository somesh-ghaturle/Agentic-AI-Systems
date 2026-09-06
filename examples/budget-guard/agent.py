"""A bounded autonomous loop where the agent chooses its next step.

The four bounds the architecture docs name -- steps, wall-clock, tokens, and no-progress --
are the four ways an autonomous loop fails to stop. The harness-agent exercises three of
them. This example exercises the one that is left: a per-request token budget.

A step budget fires after a fixed count. A token budget fires before a spend that would
exceed what remains, and that is where the two differ: a step-count limit lets the agent
*start* a step it cannot finish, a token budget does not, because the check is before the
spend, not after. The agent that spent its last tokens on a step that could not complete is
the failure mode this example exists to make visible.

The agent decides its own next step based on what it knows and how much budget remains.
When budget is tight it takes a cheaper ("quick") version of the same step, so the agent
degrades gracefully rather than hard-stopping with half an answer. When even the quick
version does not fit, it stops and names what it completed and what it never got to --
because a budget that fires without naming what was lost hides its own cost.

Run:

    python3 examples/budget-guard/agent.py "summarize the refund policy"
    python3 examples/budget-guard/agent.py "summarize the refund policy" --budget 2300
    python3 examples/budget-guard/agent.py "summarize the refund policy" --budget 500
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Simulated knowledge base -- stands in for whatever the agent reads.
# ---------------------------------------------------------------------------

KB = {
    "refund": "Refunds are issued within 30 days of purchase for unused services.",
    "policy": "The full policy is in the handbook, section 4.",
    "warranty": "Warranty claims require a proof of purchase and a description of the defect.",
    "deployment": "Deployment runs through the CI pipeline after approval.",
    "billing": "Billing questions go to finance@example.com.",
    "incident": "Incident reports are filed in the tracking system within 24 hours.",
    "security": "Security issues are reported to security@example.com and triaged within 48h.",
}


# ---------------------------------------------------------------------------
# Steps and their costs. Thorough is the default; quick is what the agent
# falls back to when budget is tight. The numbers are simulated token counts.
# ---------------------------------------------------------------------------

THOROUGH_COST = {
    "gather": 800,
    "analyze": 1200,
    "draft": 600,
    "review": 400,
    "refine": 500,
}

QUICK_COST = {
    "gather": 200,
    "analyze": 400,
    "draft": 200,
    "review": 100,
    "refine": 150,
}


# ---------------------------------------------------------------------------
# The result the agent hands back.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StepRecord:
    name: str
    cost: int
    mode: str  # "thorough" or "quick"


@dataclass(frozen=True)
class BudgetResult:
    answer: str
    completed: list[StepRecord]
    skipped: list[str]
    tokens_used: int
    budget: int
    exhausted: bool

    @property
    def finished(self) -> bool:
        return not self.skipped


# ---------------------------------------------------------------------------
# The agent.
# ---------------------------------------------------------------------------


class BudgetGuard:
    """A bounded autonomous loop that stops when its token budget is exhausted.

    The agent's goal is to answer a question by gathering context, analyzing it, drafting
    an answer, and reviewing that answer. It chooses its own next step -- it can loop back
    to gather if analysis found too little, or refine if review found a gap -- rather than
    following a fixed pipeline. The token budget is the bound that keeps the loop from
    running forever, and the cost-aware step selection is what keeps the agent from
    spending its last tokens on a step it cannot finish.

    The decision the agent makes at every step is:

        1.  What is the next step, given what I have done so far?
        2.  Can I afford the thorough version? If not, can I afford the quick one?
        3.  If neither fits, stop and name what I never got to.

    That third line is the one the architecture docs call out: a bound you have not
    exercised is a bound you have not got. The budget fires here, and what it names is
    actionable -- "skipped: review" tells you the answer is unreviewed, not merely
    "budget exhausted" which tells you nothing.
    """

    def __init__(self, request: str, token_budget: int = 3000):
        self.request = request
        self.token_budget = token_budget
        self.tokens_used = 0
        self.completed: list[StepRecord] = []
        self.skipped: list[str] = []

        # Agent state -- what it knows so far.
        self._gathered: list[str] = []
        self._analyzed = False
        self._draft = ""
        self._reviewed = False
        self._refine_count = 0
        self._max_refines = 2

    def remaining(self) -> int:
        return self.token_budget - self.tokens_used

    def _can_afford(self, step: str, quick: bool = False) -> bool:
        cost = QUICK_COST[step] if quick else THOROUGH_COST[step]
        return self.tokens_used + cost <= self.token_budget

    def _spend(self, step: str, quick: bool = False) -> StepRecord:
        cost = QUICK_COST[step] if quick else THOROUGH_COST[step]
        self.tokens_used += cost
        mode = "quick" if quick else "thorough"
        record = StepRecord(name=step, cost=cost, mode=mode)
        self.completed.append(record)
        return record

    def _next_step(self) -> str | None:
        """Decide the next step based on current state.

        This is the autonomous part: the agent looks at what it has done and decides
        what to do next, rather than following a fixed sequence. It can loop back to
        gather if analysis found too little, or to draft if review found a gap.
        """
        if not self._gathered:
            return "gather"
        if not self._analyzed:
            return "analyze"
        if not self._draft:
            return "draft"
        if not self._reviewed:
            return "review"
        # Review passed? Done. But if review found a gap and we have refine budget,
        # loop back to draft. This is the autonomous loop, not a pipeline.
        if self._refine_count < self._max_refines and not self._review_passed():
            return "refine"
        return None

    def _review_passed(self) -> bool:
        """A simple check: does the draft mention the key subject of the request?"""
        if not self._draft:
            return False
        key = self._subject()
        return bool(key) and key in self._draft.lower()

    def _subject(self) -> str:
        """Extract the subject keyword from the request (simulated classification)."""
        lowered = self.request.lower()
        for keyword in KB:
            if keyword in lowered:
                return keyword
        return ""

    def _do_gather(self, quick: bool):
        """Read from the knowledge base. Quick mode reads fewer sources."""
        if quick:
            self._gathered = [v for k, v in KB.items() if k in self.request.lower()][:1]
        else:
            self._gathered = [v for k, v in KB.items() if k in self.request.lower()]
        # If nothing matched, grab the first entry so the agent has something to work with.
        if not self._gathered:
            self._gathered = [next(iter(KB.values()))]

    def _do_analyze(self, quick: bool):
        """Reason over gathered context. Quick mode skips the sufficiency check."""
        if quick:
            self._analyzed = True
            return
        # If we gathered too little, loop back: clear the flag so _next_step sends us to gather.
        if len(self._gathered) < 1:
            self._analyzed = False
            self._gathered = []
        else:
            self._analyzed = True

    def _do_draft(self, quick: bool):
        """Produce a draft answer from the analyzed context."""
        if quick:
            self._draft = self._gathered[0] if self._gathered else "No context available."
        else:
            self._draft = " ".join(self._gathered) if self._gathered else "No context available."

    def _do_review(self, quick: bool):
        """Check the draft. Quick mode does a lighter check."""
        self._reviewed = True

    def _do_refine(self, quick: bool):
        """Refine the draft after review found a gap."""
        self._refine_count += 1
        if quick:
            self._draft = f"Refined: {self._draft}"
        else:
            key = self._subject()
            if key and key not in self._draft.lower():
                self._draft = f"{self._draft} (re: {key})"
            else:
                self._draft = f"Refined: {self._draft}"

    _HANDLERS = {
        "gather": _do_gather,
        "analyze": _do_analyze,
        "draft": _do_draft,
        "review": _do_review,
        "refine": _do_refine,
    }

    def run(self) -> BudgetResult:
        """Run the autonomous loop until done or budget exhausted."""
        while True:
            step = self._next_step()
            if step is None:
                break

            # Cost-aware selection: try thorough first, fall back to quick.
            if self._can_afford(step, quick=False):
                self._spend(step, quick=False)
                self._HANDLERS[step](self, quick=False)
            elif self._can_afford(step, quick=True):
                self._spend(step, quick=True)
                self._HANDLERS[step](self, quick=True)
            else:
                # Cannot afford even the quick version. Record what we never got to.
                remaining_steps = self._remaining_step_names(step)
                self.skipped = remaining_steps
                break

        return BudgetResult(
            answer=self._draft or "(no answer produced)",
            completed=list(self.completed),
            skipped=self.skipped,
            tokens_used=self.tokens_used,
            budget=self.token_budget,
            exhausted=bool(self.skipped),
        )

    def _remaining_step_names(self, from_step: str) -> list[str]:
        """Steps from the current one onward that will not run."""
        all_steps = ["gather", "analyze", "draft", "review", "refine"]
        done = {r.name for r in self.completed}
        return [s for s in all_steps if s not in done and s != from_step or s == from_step]


def main():
    args = sys.argv[1:]
    budget = 3000
    request = ""

    i = 0
    while i < len(args):
        if args[i] == "--budget" and i + 1 < len(args):
            budget = int(args[i + 1])
            i += 2
        else:
            request = args[i]
            i += 1

    if not request:
        request = "summarize the refund policy"

    agent = BudgetGuard(request, token_budget=budget)
    result = agent.run()

    print(f"Request: {request}")
    print(f"Budget:  {result.budget} tokens")
    print(f"Used:    {result.tokens_used} tokens")
    print(f"Status:  {'EXHAUSTED' if result.exhausted else 'COMPLETE'}")
    print()
    print("Steps:")
    for step in result.completed:
        print(f"  {step.name:8} {step.mode:8} {step.cost:4} tokens")
    if result.skipped:
        print(f"Skipped: {', '.join(result.skipped)}")
    print()
    print(f"Answer:  {result.answer}")


if __name__ == "__main__":
    main()
