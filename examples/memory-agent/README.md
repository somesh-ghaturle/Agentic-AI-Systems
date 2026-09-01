# Memory agent

This offline example composes four long-term memory patterns without credentials or
network access:

- `VectorMemory` stores fixed-size embeddings and returns nearest neighbours. Its
  interface is intentionally compatible with the subset of FAISS an agent normally uses.
- `GraphMemory` stores typed relationships, matching the useful subset of NetworkX for
  this demo.
- `TimeDecayMemory` applies exponential half-life decay and removes stale entries.
- `SessionMemory` scopes recalled facts to a session and records the session ID in metadata.

The standard-library implementation is small enough to run on a laptop or edge device.
Install `requirements.txt` and pass `use_faiss=True` or `use_networkx=True` when scale
requires the optional FAISS and NetworkX backends; keep the session and decay policy at
the application boundary.

```bash
python3 examples/memory-agent/agent.py
python3 -m unittest tests.test_memory_agent -v
```

No data is persisted and the example makes no network calls.
