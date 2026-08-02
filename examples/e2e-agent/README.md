E2E Agent Example — Secure, Observable, Auditable

This end-to-end example demonstrates a minimally complete pipeline suitable for enterprise experiments: tracing, observability, audit logs, provenance artifacts, security gating, and governance metadata.

Architecture

- FastAPI service that exposes `/invoke` and `/healthz`.
- OpenTelemetry tracing (console exporter) to demonstrate trace IDs and spans.
- Audit log (`examples/e2e-agent/audit.log`) appends structured JSON per request.
- Per-request provenance artifact saved under `examples/e2e-agent/provenance/<trace_id>.json`.

System architecture (mermaid)

```mermaid
flowchart LR
	Client[Client]
	APIGW[API Gateway / Load Balancer]
	Agent[FastAPI E2E Agent]
	OTel[OpenTelemetry Collector]
	Traces[Tracing Backend\n(Jaeger/Tempo)]
	Metrics[Metrics Backend\n(Prometheus)]
	Audit[Audit Store / SIEM]
	Provenance[Provenance Store\n(Immutable Object Storage)]
	ModelRegistry[Model Registry]
	Secrets[Secrets Manager]
	CI[CI/CD Pipeline]

	Client --> APIGW
	APIGW --> Agent
	Agent --> OTel
	OTel --> Traces
	OTel --> Metrics
	Agent --> Audit
	Agent --> Provenance
	CI --> ModelRegistry
	CI --> Agent
	Agent --> Secrets
	ModelRegistry --> Agent

	classDef infra fill:#f8f9fa,stroke:#333,stroke-width:1px
	class OTel,Traces,Metrics,Audit,Provenance,ModelRegistry,Secrets,CI infra
```

	SVG diagram (auto-generated on PR): [examples/e2e-agent/architecture.svg](examples/e2e-agent/architecture.svg)

Design guidance & 2026 reference

This example follows the 2026 agentic architecture patterns described here:
https://github.com/alirezadir/Agentic-AI-Systems/blob/main/03_system_design/2026-agentic-ai-system-design.md

Security & governance

- API key enforcement via `x-api-key` header (for demo; replace with a secrets manager in production).
- `E2E_AGENT_MODEL`, `E2E_AGENT_COMMIT` environment variables for provenance and auditability.
- Audit log and provenance files are stored in the repository under `examples/e2e-agent/` for demo; in production use immutable storage, tamper-evident logs, and RBAC.

SLA & operational controls

- Health endpoint `/healthz` for liveness probes.
- Use canary/blue-green deployments and route control for production rollouts.
- Monitor latency, error rate, and trace-based SLOs (e.g., 99th percentile latency < 200ms).

Observability

- Traces include `trace_id` and span attributes `user.id`, `model.version`, and `commit`.
- Audit logs include trace_id to link traces -> logs -> provenance.
- Replace `ConsoleSpanExporter` with OTLP exporter to send spans to your collector (Jaeger/Tempo/OpenTelemetry Collector).

How to run (local demo)

```bash
cd examples/e2e-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export E2E_AGENT_API_KEY=local-test-key
export E2E_AGENT_MODEL=v0.1-demo
export E2E_AGENT_COMMIT=local-demo
uvicorn app:app --host 0.0.0.0 --port 8000
```

Invoke (example)

```bash
curl -X POST http://localhost:8000/invoke -H "Content-Type: application/json" -H "x-api-key: local-test-key" -d '{"prompt":"Plan deployment for service X","user_id":"alice"}'
```

Audit & provenance

- Check `examples/e2e-agent/audit.log` for structured audit entries.
- Check `examples/e2e-agent/provenance/<trace_id>.json` for provenance metadata.

Notes & production hardening

- Use a secret manager (Vault, AWS Secrets Manager) for API keys, not env vars.
- Store audit logs in immutable, access-controlled storage and forward to SIEM (Splunk/Datadog/ELK).
- Sign and checksum model artifacts; record SBOM for dependencies.
- Add authentication/authorization (OIDC, mTLS) for endpoints.

This example is intentionally minimal to make the end-to-end flow easy to inspect and test. Use it as a template to build production-grade pipelines with stronger controls and monitoring.
