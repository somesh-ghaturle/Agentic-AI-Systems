# Hermes approval dashboard

This small React/FastAPI dashboard demonstrates the human-in-the-loop UX for
`hermes-agent`: operators see the tool, exact arguments, rationale, and fingerprint
before choosing **Approve** or **Reject**. WebSocket events update all open dashboards.
The backend records decisions but never executes tools.

This example makes no security claim; its in-memory store and local development transport are
not suitable for production approvals.

```bash
cd examples/hermes-dashboard
docker compose up
# open http://localhost:5173
```

For a dependency-managed local run, install `backend/requirements.txt` and run
`uvicorn backend.app:app --reload`. The in-memory store is intentionally not durable
or authenticated; use an identity provider, CSRF/origin controls, an atomic durable
approval store, and TLS before exposing it beyond localhost. The compose file is
provided for local development only and has no credentials or cloud integrations.

## What this is not

Not an authorization system. `actor` is a free-text field in the request body, so anyone who
can reach the API can approve as anyone -- including the agent that filed the proposal. The
`rationale` shown to the reviewer is also the agent's own text, which makes it a channel for
persuasion rather than evidence.

Not connected to execution. A decision is recorded and broadcast; nothing consumes it. The
guarantee that an approved action is the one that runs lives in the executor's claim, which is
`hermes-agent` and `infra/*/modules/approval`, not here.
