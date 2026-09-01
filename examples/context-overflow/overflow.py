"""Context overflow: what the model loses when the window is full.

    python3 overflow.py

This is the companion to `context-compaction`: instead of praising a compactor, it shows the
failure mode of the naive strategy most agents write first — keep the most recent N messages and
ignore the oldest decision. The result is the same shape as a real context overflow: the system
prompt, the design decision, and the unresolved question get pushed out by low-value chatter.

Standard library only, no model, no cloud.
"""

import re

# A long-running migration conversation: the architectural decision is old, the repeated tool
# output is recent, and the naive truncation keeps the latter while dropping the former.
HISTORY = [
    ("system", "You are helping a team migrate a billing service to a new database."),
    ("user", "We are moving orders off Postgres; target platform is DynamoDB."),
    ("assistant", "DECISION: Single-table design, PK=customer_id, SK=order_id#timestamp."),
    ("assistant", "OPEN QUESTION: Should refunds stay in the same table or be separate?"),
    ("assistant", "Reading schema.sql ..."),
    ("tool", "schema.sql: 412 lines, 7 tables; orders has 23 columns"),
    ("assistant", "Reading migrations/ ..."),
    ("tool", "migrations/: 47 files"),
    ("assistant", "Checking query patterns in app/orders/repository.py ..."),
    ("tool", "repository.py: 14 query methods"),
    ("assistant", "find_by_customer, find_by_status, and find_recent are all clean."),
    ("assistant", "Reading refunds usage ..."),
    ("tool", "refunds: 3 call sites, all read-only"),
    ("assistant", "Explored the refund path and verified the same key shape works."),
    ("assistant", "test run: 39 passed"),
    ("assistant", "test run: 40 passed"),
    ("assistant", "test run: 41 passed"),
    ("assistant", "test run: 42 passed"),
    ("assistant", "test run: 43 passed"),
    ("assistant", "test run: 44 passed"),
    ("assistant", "test run: 45 passed"),
    ("assistant", "test run: 46 passed"),
]


def tokens(text):
    return len(re.findall(r"\S+", text))


def total_tokens(messages):
    return sum(tokens(content) for _, content in messages)


def truncate_by_recency(messages, budget):
    """Keep the newest messages until the budget is met; oldest messages fall off first."""
    if budget < 0:
        raise ValueError("budget cannot be negative")

    kept = []
    used = 0
    for role, content in reversed(messages):
        content_tokens = tokens(content)
        if used + content_tokens > budget:
            # Stop the walk here: anything older than the current message is not kept.
            break
        kept.insert(0, (role, content))
        used += content_tokens
    return kept, {"kept": len(kept), "budget": budget, "used": used}


def keep_critical_messages(messages, budget):
    """Keep the system prompt and the decisions, then respect the budget with the rest."""
    if budget < 0:
        raise ValueError("budget cannot be negative")

    required = []
    for role, content in messages:
        if role == "system" or "DECISION:" in content or "OPEN QUESTION:" in content:
            required.append((role, content))

    remaining = [item for item in messages if item not in required]
    kept = list(required)
    used = total_tokens(kept)

    for role, content in reversed(remaining):
        content_tokens = tokens(content)
        if used + content_tokens > budget:
            continue
        kept.insert(0, (role, content))
        used += content_tokens

    return kept, {"kept": len(kept), "budget": budget, "used": used}


def main():
    budget = 80
    naive_kept, naive_stats = truncate_by_recency(HISTORY, budget)
    critical_kept, critical_stats = keep_critical_messages(HISTORY, budget)

    print(f"Window budget: {budget} tokens")
    print(f"Original history: {len(HISTORY)} messages, ~{total_tokens(HISTORY)} tokens")
    print(f"Naive truncate:   {len(naive_kept)} messages, ~{naive_stats['used']} tokens")
    print(f"Critical keep:    {len(critical_kept)} messages, ~{critical_stats['used']} tokens")
    print()

    print("Naive recency keeps the recent tool chatter:")
    for role, content in naive_kept[-5:]:
        print(f"  {role:<9} {content[:80]}")

    print("\nCritical strategy keeps the actual constraints:")
    for role, content in critical_kept:
        print(f"  {role:<9} {content[:80]}")

    print(
        "\nThe bug is visible here: the oldest decision is the one that constrains the future, "
        "and naive truncation drops it while keeping the latest test-run noise."
    )


if __name__ == "__main__":
    main()
