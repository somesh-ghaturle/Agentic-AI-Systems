Ray Orchestrator Example

A tiny example showing Ray remote tasks and aggregation.

Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run

```bash
python orchestrator.py
```

Notes

- Use Ray for distributed execution and background actor-based orchestration for heavy workloads.
- For production, integrate with Ray Serve or Ray AIR for model serving and training orchestration.

## What this is not

Not orchestration in the sense the rest of this repository means. Eight independent squarings
fan out and gather back: no dependencies between tasks, no failure handling, no retries, no
cancellation, no bound on how many run. It shows Ray's `remote`/`get` shape and nothing about
coordinating agents.

## Security

This example makes no security claim, which is why `SECURITY.md` lists it out of scope. The
read/write boundary this repository is organised around is demonstrated by `hermes-agent` and
`graph-agent`; nothing here enforces one, and none of this would be adequate as a production
service as written.
