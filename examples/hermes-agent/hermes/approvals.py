"""Approvals: bound to one action, claimed exactly once.

The property the whole repository is organised around is that a state-changing action
cannot reach production without a human approving *that specific action*. Two words there
do the work:

  **specific** — an approval carries a fingerprint of the tool name and the exact
  arguments. Approving `restart_service(name="billing")` does not approve
  `restart_service(name="payments")`, and does not approve `delete_record` at all. Without
  the binding, an approval degrades into a session-wide permission and the human is
  approving a category, not an act.

  **once** — claiming is a compare-and-set. A token that has been spent cannot be spent
  again, and two racing claims cannot both win. This is the in-process analogue of the
  claim primitive each cloud tree uses: a DynamoDB condition expression on AWS, a
  transaction on Firestore, an ETag on Cosmos. Same invariant, three implementations,
  because that is the primitive each provider gives you.

Expiry is the third control and the least interesting until it matters: an approval that
lives forever is a credential.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

DEFAULT_TTL_SECONDS = 300.0


class ApprovalError(Exception):
    """Base class for every way a claim can fail."""


class UnknownApproval(ApprovalError):
    """No approval by that token."""


class ApprovalMismatch(ApprovalError):
    """The token is real but was granted for a different action."""


class ApprovalExpired(ApprovalError):
    """The token is real and matches, and it is too old to use."""


class ApprovalAlreadyUsed(ApprovalError):
    """The token is real and matches, and it has already been spent."""


def fingerprint(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Hash the action a human is being asked to approve.

    `sort_keys` matters more than it looks: without it, two dicts that are equal in Python
    produce different fingerprints depending on insertion order, and an approval granted by
    one code path fails to match the identical action arriving by another. The failure
    would be intermittent and would look like a race.
    """
    canonical = json.dumps(
        {"tool": tool_name, "arguments": arguments}, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass
class Approval:
    token: str
    fingerprint: str
    tool: str
    arguments: Dict[str, Any]
    approver: str
    granted_at: float
    expires_at: float
    used_at: Optional[float] = None

    @property
    def used(self) -> bool:
        return self.used_at is not None

    def expired(self, now: float) -> bool:
        return now >= self.expires_at


class ApprovalStore:
    """In-memory approval records. One process, one lock, no persistence.

    A real deployment puts these in the state store the rest of the system already trusts,
    which is what the `infra/` trees do. What must survive that substitution is the
    compare-and-set in `claim`: if the backing store cannot do it atomically, the store is
    the wrong choice, not something to paper over with a read-then-write.
    """

    def __init__(self, clock: Callable[[], float] = time.time) -> None:
        self._clock = clock
        self._approvals: Dict[str, Approval] = {}
        self._lock = threading.Lock()

    def grant(
        self,
        tool: str,
        arguments: Dict[str, Any],
        approver: str,
        ttl_seconds: float = DEFAULT_TTL_SECONDS,
    ) -> Approval:
        now = self._clock()
        approval = Approval(
            token=uuid.uuid4().hex,
            fingerprint=fingerprint(tool, arguments),
            tool=tool,
            arguments=dict(arguments),
            approver=approver,
            granted_at=now,
            expires_at=now + ttl_seconds,
        )
        with self._lock:
            self._approvals[approval.token] = approval
        return approval

    def claim(self, token: str, tool: str, arguments: Dict[str, Any]) -> Approval:
        """Spend an approval for exactly this action, or raise.

        Everything happens under one lock. Checking validity and marking the token spent in
        two separate critical sections would let two callers both pass the check before
        either marked it, which is the single-use guarantee gone.
        """
        wanted = fingerprint(tool, arguments)
        now = self._clock()
        with self._lock:
            approval = self._approvals.get(token)
            if approval is None:
                raise UnknownApproval(f"no approval with token {token!r}")
            if approval.fingerprint != wanted:
                raise ApprovalMismatch(
                    f"approval {token!r} was granted for {approval.tool}"
                    f"({_render(approval.arguments)}), not {tool}({_render(arguments)})"
                )
            if approval.used:
                raise ApprovalAlreadyUsed(
                    f"approval {token!r} was already used at {approval.used_at}"
                )
            if approval.expired(now):
                raise ApprovalExpired(
                    f"approval {token!r} expired at {approval.expires_at}, now {now}"
                )
            approval.used_at = now
            return approval

    def get(self, token: str) -> Optional[Approval]:
        with self._lock:
            return self._approvals.get(token)


def _render(arguments: Dict[str, Any]) -> str:
    return ", ".join(f"{key}={value!r}" for key, value in sorted(arguments.items()))
