"""Compaction that keeps decisions and drops resolved detail.

    python3 compact.py

The point of the example is the contrast with truncation. Keeping the most recent N messages is
the obvious implementation and it is wrong in a specific way: recency and relevance are
different axes, and the decision that constrains everything downstream is usually the oldest
thing in the history.

Standard library only, no model. The classifier here is keyword-based, which is a real
simplification — a production version would use a model or explicit message tagging. What the
example is actually demonstrating is the *retention policy*, and that is worth seeing on its
own before a model is involved in applying it.
"""

import re

# A stand-in for a real agent conversation: an early architectural decision, some resolved
# back-and-forth, an unresolved question, and a lot of tool noise.
HISTORY = [
    ("system", "You are helping migrate a service to a new database."),
    ("user", "We're moving orders off Postgres. Target is DynamoDB."),
    ("assistant", "DECISION: single-table design, PK=customer_id, SK=order_id#timestamp."),
    ("assistant", "Reading schema.sql ..."),
    ("tool", "schema.sql: 412 lines, 8 tables, orders has 23 columns"),
    ("assistant", "Reading migrations/ ..."),
    ("tool", "migrations/: 47 files"),
    ("assistant", "The orders.status column is an enum with 6 values."),
    ("user", "Does status need a GSI?"),
    ("assistant", "Yes — queries filter on it. GSI1: PK=status, SK=created_at."),
    ("assistant", "Checking query patterns in app/orders/repository.py ..."),
    ("tool", "repository.py: 14 query methods"),
    ("assistant", "find_by_customer, find_by_status, find_recent all map cleanly."),
    ("assistant", "find_by_customer_and_date_range needs the SK prefix — resolved, works."),
    ("tool", "test run: 41 passed"),
    ("assistant", "OPEN QUESTION: refunds table has an FK to orders. Denormalize or keep separate?"),
    ("assistant", "Reading refunds usage ..."),
    ("tool", "refunds: 3 call sites, all read-only"),
    ("assistant", "Wrote adapters/dynamo_orders.py."),
    ("tool", "test run: 44 passed"),
]

# Rough proxy for tokens. Good enough to show a ratio; not a tokenizer.
def tokens(text):
    return len(re.findall(r"\S+", text))


def total_tokens(messages):
    return sum(tokens(content) for _, content in messages)


# --- the retention policy -------------------------------------------------------------
#
# Three categories, and only the first two survive. The ordering matters: a message is checked
# against KEEP before DROP, so "DECISION: ... resolved" is kept rather than dropped.

KEEP_MARKERS = ("DECISION:", "OPEN QUESTION:", "PK=", "GSI")
DROP_ROLES = ("tool",)
DROP_MARKERS = ("Reading ", "Checking ", "test run:")


def classify(role, content):
    """Return 'keep', 'drop', or 'summarize'.

    The system message is checked first and unconditionally kept. Running this example is what
    made that necessary: the first version classified it as ordinary prose, folded it into the
    summary line, and produced a compacted history with no instructions in it. Compaction that
    discards the system prompt has thrown away the thing the context existed to serve.
    """
    if role == "system":
        return "keep"
    if any(marker in content for marker in KEEP_MARKERS):
        return "keep"
    if role in DROP_ROLES or any(content.startswith(m) for m in DROP_MARKERS):
        return "drop"
    return "summarize"


def compact(messages, keep_recent=2):
    """Compress history: decisions verbatim, resolved detail summarized, noise dropped.

    `keep_recent` is a concession to continuity — the last couple of turns are kept whatever
    their class, because an agent resuming mid-thought needs to know what it just did. It is a
    small allowance on top of the policy, not the policy itself, which is the distinction the
    module docstring is about.
    """
    if keep_recent < 0:
        raise ValueError("keep_recent cannot be negative")

    # Written as an explicit split index rather than `messages[:-keep_recent]`, which silently
    # means "the whole list" when keep_recent is 0 — the one value where the intent is the
    # opposite.
    split = len(messages) - keep_recent
    head, tail = messages[:split], messages[split:]

    kept, summarized, dropped = [], [], []
    for role, content in head:
        verdict = classify(role, content)
        if verdict == "keep":
            kept.append((role, content))
        elif verdict == "drop":
            dropped.append((role, content))
        else:
            summarized.append((role, content))

    out = list(kept)
    if summarized:
        out.append(
            (
                "system",
                f"[compacted: {len(summarized)} exploratory message(s) and "
                f"{len(dropped)} tool result(s) omitted]",
            )
        )
    out.extend(tail)
    return out, {"kept": len(kept), "summarized": len(summarized), "dropped": len(dropped)}


def main():
    before = total_tokens(HISTORY)
    compacted, stats = compact(HISTORY)
    after = total_tokens(compacted)

    print(f"before:  {len(HISTORY):>2} messages, ~{before:>3} tokens")
    print(f"after:   {len(compacted):>2} messages, ~{after:>3} tokens")
    print(f"         {100 - after * 100 // before}% smaller  {stats}\n")

    print("What survived:")
    for role, content in compacted:
        print(f"  {role:<9} {content[:76]}")

    print("\nWhat truncation would have kept instead (last 6):")
    for role, content in HISTORY[-6:]:
        print(f"  {role:<9} {content[:76]}")

    print(
        "\nNote the difference: truncation loses the single-table DECISION and the GSI\n"
        "design — the two things that constrain every future turn — while keeping three\n"
        "tool results that are pure noise. The oldest message was the most important one."
    )


if __name__ == "__main__":
    main()
