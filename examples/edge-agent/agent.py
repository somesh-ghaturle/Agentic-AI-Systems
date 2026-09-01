#!/usr/bin/env python3
"""A local-only edge agent with SQLite state and a file approval gate.

The module intentionally imports no cloud SDK and opens no network socket.  The
default database is in memory; pass a path when deploying on a device.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import secrets
import sqlite3
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class Proposal:
    token: str
    action: str
    arguments: dict[str, Any]
    fingerprint: str
    created_at: float


def _fingerprint(action: str, arguments: dict[str, Any]) -> str:
    payload = json.dumps(
        {"action": action, "arguments": arguments}, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(payload).hexdigest()


class LocalApprovalGate:
    """Persist one exact, single-use proposal in a local JSON file."""

    def __init__(
        self, path: str | Path | None = None, clock: Callable[[], float] = time.time
    ) -> None:
        self.path = Path(path) if path is not None else None
        self._clock = clock
        self._spent: set[str] = set()

    def propose(self, action: str, arguments: dict[str, Any]) -> Proposal:
        proposal = Proposal(
            token=secrets.token_urlsafe(18),
            action=action,
            arguments=dict(arguments),
            fingerprint=_fingerprint(action, arguments),
            created_at=self._clock(),
        )
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(asdict(proposal), sort_keys=True) + "\n")
        return proposal

    def approve(self, token: str) -> Proposal:
        if self.path is None:
            raise ValueError("a file path is required to approve a proposal")
        proposal = Proposal(**json.loads(self.path.read_text()))
        if not hmac.compare_digest(token, proposal.token):
            raise PermissionError("approval token does not match the pending proposal")
        if proposal.token in self._spent:
            raise PermissionError("approval has already been used")
        self._spent.add(proposal.token)
        self.path.unlink(missing_ok=True)
        return proposal


class EdgeAgent:
    """Execute safe local reads and gate local writes behind ``LocalApprovalGate``."""

    def __init__(
        self,
        db_path: str | Path = ":memory:",
        approval_path: str | Path | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.connection = sqlite3.connect(str(db_path))
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        self.connection.commit()
        self.approvals = LocalApprovalGate(approval_path, clock=clock)

    def close(self) -> None:
        self.connection.close()

    def read(self, key: str) -> str | None:
        row = self.connection.execute("SELECT value FROM state WHERE key = ?", (key,)).fetchone()
        return row[0] if row else None

    def propose_write(self, key: str, value: str) -> Proposal:
        return self.approvals.propose("set_state", {"key": key, "value": value})

    def apply(self, proposal: Proposal) -> None:
        if proposal.action != "set_state":
            raise ValueError(f"unsupported local action: {proposal.action}")
        self.connection.execute(
            "INSERT INTO state(key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (proposal.arguments["key"], proposal.arguments["value"]),
        )
        self.connection.commit()

    def approve(self, token: str) -> dict[str, str]:
        """Claim the local proposal and apply it exactly once."""
        proposal = self.approvals.approve(token)
        self.apply(proposal)
        return self.snapshot()

    def snapshot(self) -> dict[str, str]:
        rows = self.connection.execute("SELECT key, value FROM state ORDER BY key").fetchall()
        return dict(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the offline edge-agent demo.")
    parser.add_argument("command", nargs="?", default="status", choices=("status",))
    args = parser.parse_args(argv)
    agent = EdgeAgent()
    try:
        print(json.dumps({"local": True, "command": args.command, "state": agent.snapshot()}))
    finally:
        agent.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
