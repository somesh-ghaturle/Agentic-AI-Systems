#!/usr/bin/env python3
"""E2E Agent Example

Features:
- FastAPI endpoint for agent invocation
- OpenTelemetry tracing (console exporter)
- Structured logging (JSON)
- Audit logging to `audit.log` with provenance and trace IDs
- Simple security: API key via env var, least-privilege pattern
- Produces provenance artifacts per request for audit

This is a minimal, self-contained example suitable for local testing and CI smoke checks.
"""
import os
import hmac
import json
import uuid
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

# OpenTelemetry
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter


# --- Config
# Fails closed. A default here means that anyone who deploys this without reading the README
# is authenticating against a constant published in a public repository — and it is exactly
# the demo convenience that gets copied into something real.
API_KEY = os.environ.get("E2E_AGENT_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "E2E_AGENT_API_KEY must be set. For a local demo: export E2E_AGENT_API_KEY=local-test-key"
    )
MODEL_VERSION = os.environ.get("E2E_AGENT_MODEL", "v0.1.0-demo")
COMMIT = os.environ.get("E2E_AGENT_COMMIT", "unknown-commit")
# Anchored to this file, not to the working directory. The README says to `cd` here before
# starting the server, and a repo-root-relative path under that instruction silently builds
# examples/e2e-agent/examples/e2e-agent/ and writes the audit trail into it. Nothing fails;
# the artifacts just stop being where every instruction says they are.
HERE = Path(__file__).resolve().parent
AUDIT_LOG = Path(os.environ.get("E2E_AGENT_AUDIT_LOG", HERE / "audit.log"))
PROV_DIR = Path(os.environ.get("E2E_AGENT_PROV_DIR", HERE / "provenance"))
PROV_DIR.mkdir(parents=True, exist_ok=True)

# Tracing setup
resource = Resource.create({"service.name": "e2e-agent-example"})
provider = TracerProvider(resource=resource)
processor = SimpleSpanProcessor(ConsoleSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

app = FastAPI(title="E2E Agent Example")


class InvokeRequest(BaseModel):
    prompt: str
    user_id: str | None = None


def _timestamp() -> str:
    """Timezone-aware UTC, rendered with a Z suffix.

    `utcnow()` returns a naive datetime that merely happens to hold UTC — appending "Z" to
    it is an assertion the object cannot back. This produces the identical string from a
    value that actually carries its offset.
    """
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def audit_entry(trace_id: str, payload: Dict):
    entry = {
        "trace_id": trace_id,
        "timestamp": _timestamp(),
        "payload": payload,
    }
    with open(AUDIT_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def write_provenance(trace_id: str, metadata: Dict):
    path = PROV_DIR / f"{trace_id}.json"
    with open(path, "w") as f:
        json.dump(metadata, f, indent=2)


@app.post("/invoke")
async def invoke(req: InvokeRequest, request: Request):
    # Simple API key check (do NOT hardcode in production)
    key = request.headers.get("x-api-key")
    # Constant-time: `!=` on a secret returns as soon as it finds a differing byte, which
    # leaks the length of the matching prefix to anyone who can time the response.
    if not hmac.compare_digest(key or "", API_KEY):
        raise HTTPException(status_code=401, detail="Unauthorized")

    with tracer.start_as_current_span("invoke-agent") as span:
        trace_id = format(span.get_span_context().trace_id, "032x")
        span.set_attribute("user.id", req.user_id or "anonymous")
        span.set_attribute("model.version", MODEL_VERSION)
        span.set_attribute("commit", COMMIT)

        # Simulated agent logic (replace with LLM/tool orchestration)
        prompt = req.prompt
        out = f"Simulated response for: {prompt}"
        time.sleep(0.05)  # simulate latency

        # Audit & provenance
        payload = {"prompt": prompt, "response": out, "user_id": req.user_id}
        audit_entry(trace_id, payload)
        prov = {
            "trace_id": trace_id,
            "model_version": MODEL_VERSION,
            "commit": COMMIT,
            "timestamp": _timestamp(),
            "input_sample": prompt,
            "output_sample": out,
        }
        write_provenance(trace_id, prov)

        span.add_event("audit.logged", attributes={"trace_id": trace_id})

        return {"trace_id": trace_id, "response": out}


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "model_version": MODEL_VERSION}
