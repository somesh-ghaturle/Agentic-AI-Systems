#!/usr/bin/env python3
"""Run a deterministic, offline memory demonstration."""

from __future__ import annotations

import json

from memory import GraphMemory, SessionMemory


def main() -> int:
    memory = SessionMemory(embedding_dim=3)
    memory.start("demo-session")
    memory.remember("billing service uses a connection pool", [1, 0, 0], {"kind": "fact"})
    memory.remember("restart clears the pool", [0.9, 0.1, 0], {"kind": "runbook"})
    graph = GraphMemory()
    graph.add_relationship("billing", "depends_on", "payments")
    print(
        json.dumps(
            {
                "session": memory.session_id,
                "matches": memory.recall([1, 0, 0], k=2),
                "billing_dependencies": sorted(graph.related("billing", "depends_on")),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
