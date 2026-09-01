# Edge agent proof of concept

This example is designed for an intermittently connected device. It performs local
work only: state is held in SQLite and writes require a human to approve an exact
proposal in a local JSON file. There are no cloud SDKs, credentials, telemetry
endpoints, or network calls.

```bash
python3 examples/edge-agent/agent.py
python3 -m unittest tests.test_edge_agent -v
```

For a device deployment, use a persistent path:

```python
from agent import EdgeAgent
edge = EdgeAgent("/var/lib/edge-agent/state.db", "/var/lib/edge-agent/approval.json")
proposal = edge.propose_write("mode", "safe")
# A local operator reviews approval.json and calls edge.approve(proposal.token).
```

## Container and device notes

`Dockerfile` runs as an unprivileged user and contains no cloud configuration.
On Raspberry Pi or NVIDIA Jetson, mount a device-local directory at `/data` and
pass `/data/state.db` and `/data/approval.json`. AWS IoT Greengrass can supervise
the same container as a local component; keep cloud communication in a separate,
least-privilege adapter rather than adding it to this agent.
