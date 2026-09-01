# Hermes approval dashboard

This small React/FastAPI dashboard demonstrates the human-in-the-loop UX for
`hermes-agent`: operators see the tool, exact arguments, rationale, and fingerprint
before choosing **Approve** or **Reject**. WebSocket events update all open dashboards.
The backend records decisions but never executes tools.

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
