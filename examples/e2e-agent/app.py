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
import json
import uuid
import time
from datetime import datetime
from typing import Dict

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

# OpenTelemetry
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter


# --- Config
API_KEY = os.environ.get("E2E_AGENT_API_KEY", "local-test-key")
MODEL_VERSION = os.environ.get("E2E_AGENT_MODEL", "v0.1.0-demo")
COMMIT = os.environ.get("E2E_AGENT_COMMIT", "unknown-commit")
AUDIT_LOG = "examples/e2e-agent/audit.log"
PROV_DIR = "examples/e2e-agent/provenance"
os.makedirs(PROV_DIR, exist_ok=True)

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


def audit_entry(trace_id: str, payload: Dict):
    entry = {
        "trace_id": trace_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "payload": payload,
    }
    with open(AUDIT_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def write_provenance(trace_id: str, metadata: Dict):
    path = os.path.join(PROV_DIR, f"{trace_id}.json")
    with open(path, "w") as f:
        json.dump(metadata, f, indent=2)


@app.post("/invoke")
async def invoke(req: InvokeRequest, request: Request):
    # Simple API key check (do NOT hardcode in production)
    key = request.headers.get("x-api-key")
    if key != API_KEY:
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
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "input_sample": prompt,
            "output_sample": out,
        }
        write_provenance(trace_id, prov)

        span.add_event("audit.logged", attributes={"trace_id": trace_id})

        return {"trace_id": trace_id, "response": out}


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "model_version": MODEL_VERSION}
