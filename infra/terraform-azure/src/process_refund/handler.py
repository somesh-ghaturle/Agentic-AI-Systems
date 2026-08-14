# Write tool: process a refund.
#
# Marked `access = "write"` because it moves money — irreversible and customer-visible.
# The Entra application fronting this app sets `app_role_assignment_required = true`, and
# only the approval executor's identity holds the role. Verify that rather than trust it:
#
#   az ad app show --id api://<prefix>-tool-process_refund \
#     --query "requiredResourceAccess"
#   az role assignment list --assignee <executor-identity-object-id>
#
# Be clear-eyed about what that check proves. This is ONE lock, and an app role assignment
# added in the portal opens the write path with no code change and no Terraform diff — which
# is weaker than the AWS and GCP equivalents and is why modules/entra-audit watches it.
#
# What the handler still owns:
#
#   Idempotency. Agents retry, the Logic App retries, and the executor may be replayed. A
#   refund that runs twice is a real loss, so the idempotency key travels to the payment
#   provider and the provider — not this function — collapses the duplicate.
#
#   Its own limits. The validator already checked them. Checking again here costs
#   microseconds and means a future caller that skips the gate still cannot exceed policy.

import os
import time

from agentic_trace import tracer_for
from contracts import error, ok, positive_int, require

# A ceiling this function will not exceed regardless of what it was told, expressed in
# minor units so there is no float arithmetic anywhere near money.
DEFAULT_MAX_REFUND_CENTS = 50_000

SUPPORTED_CURRENCIES = frozenset({"USD", "EUR", "GBP"})


def run(payload):
    """The handler, minus the HTTP binding. Returns (body, status)."""
    tracer = tracer_for(payload, step="process_refund")
    started = time.monotonic()

    try:
        result = _process(payload, tracer)
    except Exception as exc:  # noqa: BLE001
        # A write that failed is the case where the trace matters most — it is the evidence
        # of what was attempted against an approval that a human granted.
        tracer.step_complete(
            outcome="failure",
            latency_ms=_elapsed_ms(started),
            approval_id=payload.get("approval_id"),
            idempotency_key=payload.get("idempotency_key"),
            error=str(exc),
        )
        tracer.flush()
        return {"ok": False, "error": "write_failed", "detail": str(exc)}, 500

    tracer.step_complete(
        outcome="success" if result.get("ok") else "failure",
        latency_ms=_elapsed_ms(started),
        approval_id=payload.get("approval_id"),
        idempotency_key=payload.get("idempotency_key"),
    )
    tracer.flush()
    # A rejected write returns 400 rather than 200-with-ok-false: the executor treats any
    # non-2xx as a failure, and a validation refusal is a failure of this invocation.
    return result, (200 if result.get("ok") else 400)


def _process(payload, tracer):
    # No approval_id means this was not reached through the gate. The app role check should
    # have made that impossible; refusing here makes it impossible twice.
    identity, missing = require(payload, "approval_id", "idempotency_key")
    if missing:
        return missing

    arguments = payload.get("arguments")
    if not isinstance(arguments, dict):
        return error(
            "invalid_arguments",
            expected="arguments: object with order_id, amount_cents, currency, reason",
            received=arguments,
        )

    fields, missing = require(arguments, "order_id", "amount_cents", "currency", "reason")
    if missing:
        return missing

    amount_cents, invalid = positive_int(
        fields["amount_cents"], "amount_cents", maximum=_max_refund_cents()
    )
    if invalid:
        return invalid

    currency = str(fields["currency"]).upper()
    if currency not in SUPPORTED_CURRENCIES:
        return error(
            "unsupported_currency",
            expected=sorted(SUPPORTED_CURRENCIES),
            received=currency,
        )

    outcome = _submit_refund(
        order_id=str(fields["order_id"]),
        amount_cents=amount_cents,
        currency=currency,
        reason=str(fields["reason"]),
        idempotency_key=identity["idempotency_key"],
    )

    tracer.emit(
        "write_executed",
        action="process_refund",
        order_id=str(fields["order_id"]),
        amount_cents=amount_cents,
        currency=currency,
        approval_id=identity["approval_id"],
        provider_reference=outcome.get("provider_reference"),
        replayed=outcome.get("replayed", False),
    )

    return ok(
        action="process_refund",
        approval_id=identity["approval_id"],
        order_id=str(fields["order_id"]),
        amount_cents=amount_cents,
        currency=currency,
        provider_reference=outcome.get("provider_reference"),
        replayed=outcome.get("replayed", False),
    )


def _submit_refund(order_id, amount_cents, currency, reason, idempotency_key):
    """INTEGRATION POINT — replace with the call to your payment provider.

    Two requirements on whatever goes here, both non-negotiable:

      1. Pass `idempotency_key` to the provider as its idempotency header. Every major
         provider supports one. Retrying with the same key must return the original result,
         not create a second refund.
      2. Return the provider's reference. Without it the approval record says an action
         happened but cannot be reconciled against the provider's ledger, which is the
         difference between an audit trail and a claim.

    The stub deliberately does not simulate success. A reference implementation that
    pretends to move money is worse than one that refuses to.
    """
    raise NotImplementedError(
        "process_refund is a stub. Wire _submit_refund to your payment provider, "
        f"passing idempotency_key={idempotency_key!r} as the provider's idempotency "
        f"header for order {order_id} ({amount_cents} {currency}, reason: {reason})."
    )


def _max_refund_cents():
    try:
        return int(os.environ.get("MAX_REFUND_CENTS", DEFAULT_MAX_REFUND_CENTS))
    except ValueError:
        return DEFAULT_MAX_REFUND_CENTS


def _elapsed_ms(started):
    return int((time.monotonic() - started) * 1000)
