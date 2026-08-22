Starter Agent Example

This minimal example shows a rule-based agent you can run locally as a starting point for building more complex agentic behaviors.

Run locally

```bash
python3 agent.py "Find and plan deployment for service X"
```

Docker (optional)

Build and run the image:

```bash
docker build -t agentic-starter .
docker run --rm agentic-starter "Find components"
```

What this demonstrates

- Simple prompt handling and action routing
- How to add a runnable example to this repository

Next steps

- Replace the rule-based `respond()` with calls to model APIs or orchestration frameworks.
- Add a `docker-compose.yml` or CI smoke test for reproducibility.

## Security

This example makes no security claim, which is why `SECURITY.md` lists it out of scope. The
read/write boundary this repository is organised around is demonstrated by `hermes-agent` and
`graph-agent`; nothing here enforces one, and none of this would be adequate as a production
service as written.
