"""Minimal approval dashboard API for the offline Hermes demo.

The store is intentionally in memory. A production deployment must replace it with
an authenticated, atomic store such as the approval store used by the executor.
This service never executes a tool: it records a human decision and broadcasts it.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from dataclasses import asdict, dataclass
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


@dataclass
class Approval:
    id: str
    tool: str
    arguments: dict[str, Any]
    rationale: str
    fingerprint: str
    status: str = "pending"
    decided_by: str | None = None
    created_at: float = 0.0


class ApprovalRequest(BaseModel):
    tool: str = Field(min_length=1, max_length=200)
    arguments: dict[str, Any] = Field(default_factory=dict)
    rationale: str = Field(min_length=1, max_length=4000)
    fingerprint: str | None = None


class DecisionRequest(BaseModel):
    decision: str = Field(pattern="^(approve|reject)$")
    actor: str = Field(min_length=1, max_length=200)


app = FastAPI(title="Hermes approval dashboard", version="0.1.0")
_LOCAL_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_LOCAL_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
_approvals: dict[str, Approval] = {}
_listeners: set[WebSocket] = set()


def _fingerprint(tool: str, arguments: dict[str, Any]) -> str:
    payload = json.dumps(
        {"tool": tool, "arguments": arguments}, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def _public(approval: Approval) -> dict[str, Any]:
    return asdict(approval)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/approvals")
def list_approvals() -> list[dict[str, Any]]:
    return [_public(item) for item in _approvals.values()]


@app.post("/approvals", status_code=201)
async def create_approval(request: ApprovalRequest) -> dict[str, Any]:
    expected = _fingerprint(request.tool, request.arguments)
    if request.fingerprint is not None and not hmac.compare_digest(request.fingerprint, expected):
        raise HTTPException(status_code=400, detail="fingerprint does not match tool arguments")
    approval = Approval(
        id=secrets.token_urlsafe(12),
        tool=request.tool,
        arguments=dict(request.arguments),
        rationale=request.rationale,
        fingerprint=expected,
        created_at=time.time(),
    )
    _approvals[approval.id] = approval
    await _broadcast({"event": "approval.created", "approval": _public(approval)})
    return _public(approval)


@app.post("/approvals/{approval_id}/decision")
async def decide(approval_id: str, request: DecisionRequest) -> dict[str, Any]:
    approval = _approvals.get(approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail="approval not found")
    if approval.status != "pending":
        raise HTTPException(status_code=409, detail="approval has already been decided")
    approval.status = request.decision
    approval.decided_by = request.actor
    await _broadcast({"event": "approval.decided", "approval": _public(approval)})
    return _public(approval)


@app.websocket("/ws")
async def updates(websocket: WebSocket) -> None:
    if websocket.headers.get("origin") not in (*_LOCAL_ORIGINS, None):
        await websocket.close(code=1008)
        return
    await websocket.accept()
    _listeners.add(websocket)
    await websocket.send_json({"event": "snapshot", "approvals": list_approvals()})
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        _listeners.discard(websocket)


async def _broadcast(message: dict[str, Any]) -> None:
    disconnected: list[WebSocket] = []
    for listener in _listeners:
        try:
            await listener.send_json(message)
        except (RuntimeError, WebSocketDisconnect):
            disconnected.append(listener)
    _listeners.difference_update(disconnected)
