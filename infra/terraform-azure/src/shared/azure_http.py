# Outbound HTTP with an identity attached, and inbound request parsing.
#
# ---------------------------------------------------------------------------
# Why every outbound call to another tool carries a bearer token
# ---------------------------------------------------------------------------
#
# The read/write split in this tree is drawn by Entra app roles. Each tool app is fronted by
# `auth_settings_v2` with `require_authentication = true`, and its Entra application sets
# `app_role_assignment_required = true`, so Easy Auth rejects a caller that has not been
# assigned a role on that app — before any handler code runs.
#
# The token has to be requested for the TARGET's scope, `api://<app-id-uri>/.default`. A
# token minted for a different resource is a perfectly valid token that this app rejects,
# and the 401 looks identical to "not authenticated at all". Reusing one tool's token to
# call another does not work, by design.
#
# ---------------------------------------------------------------------------
# The honest caveat, restated from ARCHITECTURE.md
# ---------------------------------------------------------------------------
#
# This is ONE lock. On AWS the orchestrator physically lacks lambda:InvokeFunction on the
# write tools; on GCP a deny policy overrides any allow that might be added later. Here, an
# app role assignment added in the portal opens the write path with no code change and no
# Terraform diff — which is exactly why modules/entra-audit exists as a detective control
# and why tests/test_write_boundary.py asserts the flag is never set to false.

import json
import os

_DEFAULT_TIMEOUT_SECONDS = 30
_credential = None


def _token_for(scope):
    """A bearer token for `scope`, from the app's user-assigned managed identity.

    AZURE_CLIENT_ID is set by modules/tools and modules/approval. Without it
    DefaultAzureCredential picks whichever identity it finds first, which on an app with
    more than one attached is a coin flip that fails intermittently.
    """
    global _credential
    if _credential is None:
        from azure.identity import DefaultAzureCredential  # noqa: PLC0415

        _credential = DefaultAzureCredential(
            managed_identity_client_id=os.environ.get("AZURE_CLIENT_ID")
        )
    return _credential.get_token(scope).token


def post_with_identity(url, payload, scope=None, timeout=_DEFAULT_TIMEOUT_SECONDS):
    """POSTs `payload` as JSON, authenticated as this app's managed identity.

    Returns (status_code, parsed_body). A non-JSON body comes back as {"raw": "..."} rather
    than raising, because a 500 from a callee is information the caller needs to record and
    losing it to a JSONDecodeError helps nobody.
    """
    import requests  # noqa: PLC0415

    headers = {"Content-Type": "application/json"}
    if scope:
        headers["Authorization"] = f"Bearer {_token_for(scope)}"

    response = requests.post(url, json=payload, headers=headers, timeout=timeout)

    try:
        body = response.json()
    except ValueError:
        body = {"raw": response.text[:1000]}

    return response.status_code, body


def resolve_callback(callback_url, outcome_payload, timeout=_DEFAULT_TIMEOUT_SECONDS):
    """Resumes a suspended Logic App run.

    The run is genuinely suspended at its `limit`-bounded webhook action — not polling, not
    sleeping — and this POST is the only thing that resumes it. If it never arrives the run
    sits until the approval window expires and the workflow records `approval_abandoned`.

    No scope is passed: a Logic App callback URL carries its own SAS signature in the query
    string, so the URL itself is the credential. That is also why the URL must be treated as
    a secret — it is written to the approval record and never logged.
    """
    return post_with_identity(callback_url, outcome_payload, scope=None, timeout=timeout)


def request_json(req):
    """Parses an azure.functions.HttpRequest body into a dict.

    Defensive on purpose. A handler that raises on a malformed body returns a 500, and a 500
    from the validator is indistinguishable — from the orchestrator's side — from the
    validator being down. Returning {} lets the handler produce a structured error the
    caller can act on instead.
    """
    if req is None:
        return {}

    try:
        body = req.get_json()
    except (ValueError, AttributeError):
        body = None

    if isinstance(body, dict):
        return body

    raw = None
    try:
        raw = req.get_body()
    except AttributeError:
        pass

    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except (TypeError, ValueError):
            pass

    return {}


def json_response(body, status=200):
    """The azure.functions return shape."""
    import azure.functions as func  # noqa: PLC0415

    return func.HttpResponse(
        json.dumps(body, default=str),
        status_code=status,
        mimetype="application/json",
    )


def require_env(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is not set on this function app.")
    return value
