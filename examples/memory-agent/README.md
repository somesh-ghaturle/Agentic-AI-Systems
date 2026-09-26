# Memory agent

This offline example composes four long-term memory patterns without credentials or
network access:

- `VectorMemory` stores fixed-size embeddings and returns nearest neighbours. Its
  interface is intentionally compatible with the subset of FAISS an agent normally uses.
- `GraphMemory` stores typed relationships, matching the useful subset of NetworkX for
  this demo.
- `TimeDecayMemory` applies exponential half-life decay and removes stale entries.
- `SessionMemory` requires a session before it stores anything and tags each fact with the
  session ID in metadata. Recall does not filter by it -- see below.

The standard-library implementation is small enough to run on a laptop or edge device.
Install `requirements.txt` and pass `use_faiss=True` or `use_networkx=True` when scale
requires the optional FAISS and NetworkX backends; keep the session and decay policy at
the application boundary.

```bash
python3 examples/memory-agent/agent.py
python3 -m unittest tests.test_memory_agent -v
```

No data is persisted and the example makes no network calls.

This example makes no security claim; production memory systems need explicit retention,
authorization, and tenant-isolation controls.

## What this is not

Not session isolation. `SessionMemory.recall()` searches every stored record, whichever session
wrote it; the session ID is recorded in metadata and is never used as a filter. A
multi-tenant store built on this would leak across tenants. The `recent` store is keyed by
session, so each `remember()` replaces the previous entry rather than adding to it.

Not embeddings, either: the demo's vectors are hand-written three-number lists. The retrieval
maths is real; the semantics are whatever vectors you supply.
