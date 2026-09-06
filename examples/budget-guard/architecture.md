# Architecture

> **[Interactive architecture diagram](../../docs/diagrams/budget-guard-architecture.html)** — open in browser for the full interactive view.

## The decision this example exists to make

The four bounds the architecture docs name -- steps, wall-clock, tokens, and no-progress -- are four ways an autonomous loop fails to stop. The harness-agent exercises three. The question this example answers is: what does the token bound look like when it is the one that fires?

The answer is that it fires *before* a spend, not after. A step-count limit lets the agent start a step it cannot finish; a token budget checked before the spend does not. That distinction is the whole reason the example exists.

## Why an autonomous loop, not a pipeline

A pipeline with a budget is a for-loop with a break. An autonomous loop with a budget is a decision: the agent looks at its state, picks the next step, checks whether it can afford it, and either runs it or stops. The difference is visible when the agent loops back -- gather again because analysis found too little, or refine because review found a gap -- because each loop-back is a step the budget has to cover.

If the example were a pipeline, the budget would fire at a fixed position every time, which is the one case a step count already handles. Making the loop autonomous is what makes the token budget earn its keep: the number of steps varies, so the bound has to be on cost, not count.

## Why quick mode

The agent falls back to a cheaper ("quick") version of a step when the thorough version does not fit. The alternative is to hard-stop the moment the thorough cost exceeds the remaining budget, which gives you half an answer and no indication of which half.

Quick mode is the graceful-degradation layer. It does not make the answer better; it makes the agent *finish* rather than *abort*, and the difference between a finished answer and an aborted one is the difference between "the budget was tight and the answer is shorter" and "the budget ran out and there is no answer."

## Why naming what was skipped

When even the quick version does not fit, the agent stops and names the steps it never ran. This is the lesson from HARNESS-ENGINEERING.md: "bounds you have not exercised are bounds you have not got." A budget that fires and says "exhausted" tells you nothing actionable. A budget that fires and says "skipped: review" tells you the answer is unreviewed, which is a fact about the answer's quality, not about the budget's size.

## What is deliberately not here

- **No model.** The agent uses keyword matching against a simulated knowledge base. The point is the budget mechanic, not the reasoning quality. Swap the handlers for model calls and the budget logic is unchanged.
- **No approval flow.** This example makes no security claim. The [harness-agent](../harness-agent/README.md) covers the write boundary; this one covers the token boundary.
- **No persistence.** The budget is per-request. Cross-request state and crash recovery are the [checkpoint-agent](../checkpoint-agent/README.md)'s subject.
