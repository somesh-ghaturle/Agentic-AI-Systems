# Firestore access for the approval records.
#
# This is the GCP counterpart of terraform-aws/src/shared/ddb.py, and the two solve
# different problems, which is worth stating because the file name suggests otherwise.
#
# `ddb.py` exists because DynamoDB has no float type: boto3's serializer raises on one
# outright, and every value written originates outside our control — the arguments a model
# proposed, the JSON a write tool returned. Unnormalized, the write raises and the approval
# record is never written, which is the one record the system cannot afford to lose.
#
# Firestore has no such problem. It stores IEEE-754 doubles natively and round-trips them,
# so there is nothing to marshal.
#
# What Firestore does need, and DynamoDB gets for free, is the CLAIM. DynamoDB expresses
# "update this record only if its status is still pending" as a ConditionExpression on a
# single API call — one atomic compare-and-set. Firestore has no conditional update at all:
# the equivalent is a transaction that reads, decides, and writes, and Firestore aborts and
# retries it if the document changed underneath.
#
# That transaction is the whole reason this module exists. Get it wrong and a
# double-clicked approve button runs the refund twice.

import os
import time

_client = None


def client():
    """The Firestore client, created once per container.

    Imported lazily so a handler running under test does not require the library.
    """
    global _client
    if _client is None:
        from google.cloud import firestore  # noqa: PLC0415

        _client = firestore.Client(
            project=os.environ.get("GCP_PROJECT"),
            database=os.environ.get("APPROVALS_DATABASE", "(default)"),
        )
    return _client


def approvals_collection(db=None):
    db = db or client()
    return db.collection(os.environ.get("APPROVALS_COLLECTION", "approvals"))


def claim(approval_id, new_status, callback_url, approver, comment=None, db=None):
    """Claims an approval record for this callback.

    Returns (previous_record, previous_status), or (None, None) if it could not be claimed.

    Stamping the callback URL here is what ties the record to one execution: a second
    callback carrying a different URL for the same approval finds the record already
    claimed and does nothing.

    A record is claimable in two cases. The ordinary one is `pending`. The other is an
    `executing` record whose claim has gone stale — an executor that died between claiming
    and resolving the callback, which would otherwise leave the workflow suspended until
    its approval window closes. Reclaiming is safe precisely because the write tool is
    idempotent on the approval ID: re-invoking with the same key returns the original
    result rather than acting twice. That property is what this recovery is built on, so a
    write tool that ignores its idempotency key breaks it.

    ---------------------------------------------------------------------------
    Why a transaction rather than a plain update
    ---------------------------------------------------------------------------

    Read-then-write without one is a race with a very specific shape: two executors both
    read `pending`, both decide they may proceed, and both invoke the write tool. The
    window is milliseconds wide and a double-clicked approve button lands squarely in it.

    Firestore's transaction gives the same guarantee DynamoDB's ConditionExpression does —
    the write applies only if nothing else touched the document since the read — by
    aborting and re-running the function when it did. Which is why everything inside
    `_txn` must be free of side effects: it can run more than once. The write tool is
    invoked by the caller AFTER this returns, never from inside.
    """
    db = db or client()
    from google.cloud import firestore  # noqa: PLC0415

    ref = approvals_collection(db).document(approval_id)
    stale_before = _iso_seconds_ago(stale_claim_seconds())

    # Mutable cell rather than a return value: the transactional function's return is
    # consumed by the Firestore decorator, not by us.
    captured = {}

    @firestore.transactional
    def _txn(transaction):
        snapshot = ref.get(transaction=transaction)
        if not snapshot.exists:
            captured["record"] = None
            return

        record = snapshot.to_dict() or {}
        status = record.get("status")

        claimable = status == "pending" or (
            status == "executing"
            # ISO-8601 UTC sorts lexicographically in timestamp order, so a string
            # comparison is a time comparison. A record with no claimed_at at all is not
            # reclaimable — fail-safe, and only reachable for records written before this
            # field existed.
            and isinstance(record.get("claimed_at"), str)
            and record["claimed_at"] < stale_before
        )
        if not claimable:
            captured["record"] = None
            return

        now = _now_iso()
        update = {
            "status": new_status,
            "callback_url": callback_url,
            "approver": approver or {},
            "claimed_at": now,
            "resolved_at": now,
        }
        if comment is not None:
            update["approver_comment"] = comment

        transaction.update(ref, update)

        # Captured before the update lands, mirroring DynamoDB's ReturnValues=ALL_OLD: the
        # fields the executor needs (action, arguments, fingerprint) are written once by
        # the validator and never revised, and the pre-update status is what tells the
        # caller a reclaim happened.
        captured["record"] = record
        captured["status"] = status

    _txn(db.transaction())

    record = captured.get("record")
    return (record, captured.get("status")) if record is not None else (None, None)


def get(approval_id, db=None):
    snapshot = approvals_collection(db).document(approval_id).get()
    return snapshot.to_dict() or {} if snapshot.exists else {}


def put(approval_id, record, db=None):
    approvals_collection(db).document(approval_id).set(record)


def record_outcome(approval_id, status, outcome, db=None):
    approvals_collection(db).document(approval_id).update(
        {
            "status": status,
            "outcome": outcome,
            "completed_at": _now_iso(),
        }
    )


def stale_claim_seconds():
    """How long an `executing` claim may sit before another executor may take it over.

    Must exceed the write tool's own timeout plus its retries, or a slow-but-alive
    execution gets a second executor running alongside it. The idempotency key makes that
    survivable rather than catastrophic, but it is still not what you want.
    """
    try:
        return int(os.environ.get("STALE_CLAIM_SECONDS", 900))
    except ValueError:
        return 900


def _iso_seconds_ago(seconds):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - seconds))


def _now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
