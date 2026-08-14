# Cosmos DB access for the approval records.
#
# The counterpart of terraform-aws/src/shared/ddb.py and terraform-gcp/src/shared/
# firestore_io.py. All three exist for the same reason — the approval record is the one
# document the system cannot afford to lose or double-write — and all three solve the CLAIM
# differently, because the primitive each database offers is different:
#
#   DynamoDB   ConditionExpression on UpdateItem — one atomic compare-and-set.
#   Firestore  a transaction that reads, decides, writes, and retries on conflict.
#   Cosmos DB  an ETag and `if_match`. Optimistic concurrency: read the document, get its
#              _etag, and send the replace back with that ETag. If anything wrote in
#              between, the ETag moved and Cosmos rejects the replace with a 412.
#
# The 412 is the whole point. Without `if_match` a replace is last-write-wins, so two
# executors that both read `pending` both succeed and the refund runs twice. The window is
# milliseconds wide and a double-clicked approve button lands squarely in it.
#
# One Cosmos-specific hazard worth naming: every read and write here passes the partition
# key explicitly. The container is partitioned on /approval_id, so a point read needs both
# the id and the partition key value — they happen to be the same string here, which makes
# it easy to omit one and get a cross-partition query that is slower, costlier, and returns
# nothing useful when the container grows.

import os
import time

_client = None
_container = None


def container():
    """The Cosmos container client, created once per worker.

    Authenticates with the function app's user-assigned managed identity — there is no key
    in app settings to leak, and modules/approval grants the data-plane role rather than
    handing out the account key.
    """
    global _client, _container
    if _container is not None:
        return _container

    from azure.cosmos import CosmosClient  # noqa: PLC0415
    from azure.identity import DefaultAzureCredential  # noqa: PLC0415

    if _client is None:
        _client = CosmosClient(
            url=_require("COSMOS_ENDPOINT"),
            # AZURE_CLIENT_ID is set by modules/approval to the user-assigned identity.
            # Without it DefaultAzureCredential picks whichever identity it finds first,
            # which on an app with more than one attached is a coin flip.
            credential=DefaultAzureCredential(
                managed_identity_client_id=os.environ.get("AZURE_CLIENT_ID")
            ),
        )

    # COSMOS_DATABASE and APPROVALS_CONTAINER are the names modules/approval actually sets
    # in app_settings. Reading a differently-named variable here would fail at the first
    # request rather than at deploy, so they are matched exactly.
    _container = _client.get_database_client(
        _require("COSMOS_DATABASE")
    ).get_container_client(_require("APPROVALS_CONTAINER"))
    return _container


def claim(approval_id, new_status, callback_url, approver, comment=None):
    """Claims an approval record for this callback.

    Returns (previous_record, previous_status), or (None, None) if it could not be claimed.

    Stamping the callback URL here is what ties the record to one run: a second callback
    carrying a different URL for the same approval finds the record already claimed and does
    nothing.

    A record is claimable in two cases. The ordinary one is `pending`. The other is an
    `executing` record whose claim has gone stale — an executor that died between claiming
    and resolving the callback, which would otherwise leave the Logic App suspended until
    its approval window closes. Reclaiming is safe precisely because the write tool is
    idempotent on the approval ID: re-invoking with the same key returns the original result
    rather than acting twice. That property is what this recovery rests on, so a write tool
    that ignores its idempotency key breaks it.

    The read-decide-replace below is NOT a transaction. It is optimistic concurrency: the
    ETag read at the top must still be current when the replace lands, or Cosmos returns 412
    and this function reports the record as unclaimable — which is the correct answer,
    because somebody else claimed it.
    """
    from azure.cosmos import exceptions  # noqa: PLC0415

    try:
        record = container().read_item(item=approval_id, partition_key=approval_id)
    except exceptions.CosmosResourceNotFoundError:
        return None, None

    status = record.get("status")
    stale_before = _iso_seconds_ago(stale_claim_seconds())

    claimable = status == "pending" or (
        status == "executing"
        # ISO-8601 UTC sorts lexicographically in timestamp order, so a string comparison is
        # a time comparison. A record with no claimed_at at all is not reclaimable —
        # fail-safe, and only reachable for records written before this field existed.
        and isinstance(record.get("claimed_at"), str)
        and record["claimed_at"] < stale_before
    )
    if not claimable:
        return None, None

    # Captured before mutation, mirroring DynamoDB's ReturnValues=ALL_OLD: the fields the
    # executor needs (action, arguments, fingerprint) are written once by the validator and
    # never revised, and the pre-update status is what tells the caller a reclaim happened.
    previous = dict(record)

    now = _now_iso()
    record.update(
        {
            "status": new_status,
            "callback_url": callback_url,
            "approver": approver or {},
            "claimed_at": now,
            "resolved_at": now,
        }
    )
    if comment is not None:
        record["approver_comment"] = comment

    try:
        container().replace_item(
            item=approval_id,
            body=record,
            # The concurrency control. Drop this and the claim silently stops working.
            etag=previous.get("_etag"),
            match_condition=_if_match(),
        )
    except exceptions.CosmosAccessConditionFailedError:
        # 412: somebody claimed it between the read and the replace.
        return None, None

    return previous, status


def get(approval_id):
    from azure.cosmos import exceptions  # noqa: PLC0415

    try:
        return container().read_item(item=approval_id, partition_key=approval_id)
    except exceptions.CosmosResourceNotFoundError:
        return {}


def put(record):
    """Creates or replaces a record. `id` is required by Cosmos and mirrors approval_id."""
    body = dict(record)
    body.setdefault("id", body["approval_id"])
    container().upsert_item(body=body)


def record_outcome(approval_id, status, outcome):
    """Records the write tool's result.

    Deliberately NOT ETag-guarded. The write already happened; refusing to record it because
    the document moved would lose the only evidence that it did.
    """
    record = get(approval_id)
    if not record:
        return
    record.update({"status": status, "outcome": outcome, "completed_at": _now_iso()})
    container().replace_item(item=approval_id, body=record)


def _if_match():
    from azure.core import MatchConditions  # noqa: PLC0415

    return MatchConditions.IfNotModified


def stale_claim_seconds():
    """How long an `executing` claim may sit before another executor may take it over.

    Must exceed the write tool's own timeout plus its retries, or a slow-but-alive execution
    gets a second executor running alongside it. The idempotency key makes that survivable
    rather than catastrophic, but it is still not what you want.
    """
    try:
        return int(os.environ.get("STALE_CLAIM_SECONDS", 900))
    except ValueError:
        return 900


def _require(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is not set on this function app.")
    return value


def _iso_seconds_ago(seconds):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - seconds))


def _now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
