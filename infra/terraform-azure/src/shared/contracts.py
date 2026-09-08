# Structured results and errors — BUILDING-BLOCKS.md section 2, "tools return contracts"
#
# "Return a structured contract, never free-form text." The reason is narrow and
# practical: a typed object either validates or it does not, and an error the model can
# read is an error the model can correct.
#
#   {"error": "invalid_date_format", "expected": "YYYY-MM-DD", "received": "next tuesday"}
#
# tells the model what to do differently. "500 Internal Server Error" tells it to retry
# the same thing until the loop bound stops it.

import hashlib
import json


def ok(**fields):
    return {"ok": True, **fields}


def error(code, expected=None, received=None, remediation=None, **fields):
    """An error the caller can act on.

    `code` is a stable machine-readable slug, not a sentence. Prose belongs in
    `remediation`, which is advisory.
    """
    payload = {"ok": False, "error": code}
    if expected is not None:
        payload["expected"] = expected
    if received is not None:
        payload["received"] = _summarize(received)
    if remediation is not None:
        payload["remediation"] = remediation
    payload.update(fields)
    return payload


def require(mapping, *names):
    """Returns (values, error). Missing fields produce one error naming all of them."""
    missing = [n for n in names if mapping.get(n) in (None, "")]
    if missing:
        return None, error(
            "missing_required_fields",
            expected=list(names),
            received=sorted(k for k in mapping if mapping.get(k) not in (None, "")),
            missing=missing,
        )
    return {n: mapping[n] for n in names}, None


def positive_int(value, field, maximum=None):
    """Integers from a model arrive as strings often enough to be worth handling."""
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None, error(
            "invalid_type", expected=f"{field}: positive integer", received=value
        )
    if parsed <= 0:
        return None, error(
            "value_out_of_range", expected=f"{field} > 0", received=parsed
        )
    if maximum is not None and parsed > maximum:
        return None, error(
            "value_out_of_range", expected=f"{field} <= {maximum}", received=parsed
        )
    return parsed, None


def fingerprint(action, arguments):
    """A stable hash of the action and arguments a human approved.

    The executor compares this against what it is about to run. Approving a $50 refund and
    executing a $5,000 one differs by one field, and one field is exactly what a hash
    catches.

    The action is bound in, not the arguments alone. The executor reads `action` and
    `arguments` back from the same stored record and invokes whichever write tool the action
    names, so hashing only the arguments leaves half of what runs unverified: an attacker who
    can rewrite the stored arguments — the only threat this check exists for — can instead
    leave them untouched and change the action. The examples this tree mirrors bind the tool
    name for the same reason (examples/hermes-agent, examples/second-path).

    Changing what goes into the hash invalidates fingerprints already stored, and that lands
    in two places. Approvals in flight across the deploy fail their tamper check as
    `arguments_tampered`, which is the safe direction. The deterministic approval ID moves
    with it — `_approval_id()` seeds a UUID5 from this digest — so a validation retried
    across the deploy stops collapsing onto the pending approval its earlier attempt created
    and opens a second one instead. That half fails open: a duplicate review to dismiss, not
    an unapproved write. Drain the approvals in flight, or expect both for one deploy.
    """
    canonical = json.dumps(
        {"action": action, "arguments": arguments},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _summarize(value, limit=200):
    """Errors travel back into a prompt. Do not paste an entire payload into one."""
    text = value if isinstance(value, str) else json.dumps(value, default=str)
    return text if len(text) <= limit else text[:limit] + "…"
