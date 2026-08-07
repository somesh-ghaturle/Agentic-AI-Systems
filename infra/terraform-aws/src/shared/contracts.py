# Structured results and errors — BUILDING-BLOCKS.md §2, "tools return contracts"
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


def fingerprint(arguments):
    """A stable hash of the arguments a human approved.

    The executor compares this against what it is about to run. Approving a $50 refund and
    executing a $5,000 one differs by one field, and one field is exactly what a hash
    catches.
    """
    canonical = json.dumps(arguments, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _summarize(value, limit=200):
    """Errors travel back into a prompt. Do not paste an entire payload into one."""
    text = value if isinstance(value, str) else json.dumps(value, default=str)
    return text if len(text) <= limit else text[:limit] + "…"
