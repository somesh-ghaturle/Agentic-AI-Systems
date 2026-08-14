# Outbound HTTP with an identity attached, and inbound request parsing.
#
# ---------------------------------------------------------------------------
# Why every outbound call here carries an OIDC token
# ---------------------------------------------------------------------------
#
# The read/write split in this tree is drawn by `roles/run.invoker` on each function's
# Cloud Run service. That check happens at the platform edge, before any handler code runs,
# and it reads the caller's identity out of a signed OIDC token whose **audience is the
# target URL**.
#
# Two failure modes follow, and neither produces an obvious error message:
#
#   1. A plain unauthenticated POST gets a 403 that looks like the URL is wrong.
#   2. A token minted for the wrong audience is a valid token that the target rejects,
#      which produces the same 403. Reusing one function's token to call another is the
#      natural way to do this and it does not work — by design, because a token that worked
#      anywhere would make the invoker check decorative.
#
# So `post_with_identity` mints a token per target URL. That is one metadata-server round
# trip per distinct callee, cached by the library, and it is what makes the boundary in
# modules/tools real from the calling side.

import json
import os

_DEFAULT_TIMEOUT_SECONDS = 30


def post_with_identity(url, payload, timeout=_DEFAULT_TIMEOUT_SECONDS):
    """POSTs `payload` as JSON, authenticated as this function's service account.

    Returns (status_code, parsed_body). A non-JSON body comes back as {"raw": "..."} rather
    than raising, because a 500 from a callee is information the caller needs to record,
    and losing it to a JSONDecodeError helps nobody.
    """
    import google.auth.transport.requests  # noqa: PLC0415
    import google.oauth2.id_token  # noqa: PLC0415

    request = google.auth.transport.requests.Request()

    # The audience is the target URL. See the note at the top of this file: this is the
    # line that makes the token usable at exactly one callee and nowhere else.
    token = google.oauth2.id_token.fetch_id_token(request, url)

    import requests  # noqa: PLC0415

    response = requests.post(
        url,
        json=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        timeout=timeout,
    )

    try:
        body = response.json()
    except ValueError:
        body = {"raw": response.text[:1000]}

    return response.status_code, body


def resolve_callback(callback_url, outcome_payload, timeout=_DEFAULT_TIMEOUT_SECONDS):
    """Resumes a suspended workflow execution.

    The workflow is genuinely suspended at `events.await_callback` — not polling, not
    sleeping — and this POST is the only thing that resumes it. If it never arrives the
    execution sits until its approval window expires and the workflow records
    `approval_abandoned`.

    Callback URLs are themselves IAM-protected, so this needs the same OIDC token as any
    other call. The orchestrator's own service account holds `workflows.invoker`; the
    executor reaches the callback because the URL was handed to it, and the platform still
    checks who is calling.
    """
    return post_with_identity(callback_url, outcome_payload, timeout=timeout)


def request_json(request):
    """Parses a functions-framework request body into a dict.

    Defensive on purpose. A handler that raises on a malformed body returns a 500, and a
    500 from the validator is indistinguishable — from the workflow's side — from the
    validator being down. Returning {} lets the handler produce a structured error the
    caller can act on instead.
    """
    if request is None:
        return {}

    try:
        body = request.get_json(silent=True)
    except Exception:  # noqa: BLE001
        body = None

    if isinstance(body, dict):
        return body

    # Some callers send a JSON string rather than an object. Cheap to accept.
    raw = getattr(request, "data", None)
    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except (TypeError, ValueError):
            pass

    return {}


def json_response(body, status=200):
    """The functions-framework return shape: (body, status, headers)."""
    return (json.dumps(body, default=str), status, {"Content-Type": "application/json"})


def require_env(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is not set on this function.")
    return value
