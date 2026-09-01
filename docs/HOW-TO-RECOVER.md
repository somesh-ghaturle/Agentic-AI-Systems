# How to Recover

Three things in this stack can fail in a way that needs recovering: Terraform's own state,
the execution-state store each orchestrator reads and writes, and a stuck approval claim. A
fourth thing — the archive — is built the opposite way on purpose; see the last section for
why "recovering" it isn't the right frame.

This is an operational runbook, not a design document. Every setting named below is read
from the tree itself, not assumed — check [THREAT-MODEL.md](THREAT-MODEL.md) for what these
controls defend against and [SECRETS-ROTATION.md](SECRETS-ROTATION.md) for what rotates.

## Before you need this

All four trees apply against a **local** Terraform state file today. AWS, Azure, and GCP each
have a `backend "s3"/"azurerm"/"gcs"` block written out and commented in every `envs/*/main.tf`
— an aspirational sketch, not active configuration. Azure additionally declares
`backend "local" {}` explicitly. Snowflake has no backend block at all, commented or otherwise,
in any environment.

`*.tfstate` and `*.tfstate.*` are gitignored, so none of this is backed up by version control.
The only copy of Terraform's own state lives on whichever machine last ran `apply`. If that
disk is lost, there is no `terraform state pull` to fall back on — recovery means
`terraform import` for every resource, by hand, one at a time, starting with `modules/state`
and `modules/approval` since most other modules reference them. Uncommenting the backend block
for your environment before that happens is cheaper than reconstructing state after.

## Terraform's own state (local backend, all four trees)

- **Locked by a crashed apply.** The local backend writes a `.terraform.tfstate.lock.info`
  file beside the state; a process that dies mid-apply leaves it behind, and the next
  `plan`/`apply` refuses to run. Confirm nothing is actually still applying, then
  `terraform force-unlock <LOCK_ID>` — the ID is printed in the lock error.
- **Corrupted mid-write.** The local backend keeps `terraform.tfstate.backup`, the state as it
  was before the last write. `cp terraform.tfstate.backup terraform.tfstate` restores it;
  anything applied since that backup is gone from the state file, though the underlying cloud
  resources still exist and can be re-imported.
- **Lost entirely.** No remote copy exists today (see above). Rebuild with
  `terraform import <resource.address> <cloud-id>` per resource.

## AWS

**Execution state** (`aws_dynamodb_table.execution_state`, `modules/state`). Point-in-time
recovery is **off in dev, on in staging and prod**
(`infra/terraform-aws/envs/*/main.tf`, `point_in_time_recovery`). Restoring PITR always creates
a **new** table — it does not repair the existing one in place:

```bash
aws dynamodb restore-table-to-point-in-time \
  --source-table-name <name_prefix>-execution-state \
  --target-table-name <name_prefix>-execution-state-restored \
  --restore-date-time <ISO8601 timestamp>
```

Point the orchestrator at the restored table (or rename tables) once you've confirmed it's
good. In dev, with PITR off, a corrupted row is not recoverable at all — resume the execution
instead of trying to repair its state.

**Stuck approval claim.** `STALE_CLAIM_SECONDS` (default 900s) is an **environment variable on
the executor Lambda** — there is no Terraform variable for it in this module
(`modules/approval/README.md`). Once the window passes, the next executor's conditional write
against the approvals table succeeds and takes the claim over automatically; nothing to run by
hand unless you want the window itself changed, which is an edit to the Lambda's environment
block.

## Azure

**Execution state** (`azurerm_storage_table.execution_state`, `modules/state`) **has no
configured recovery mechanism today.** The module's `soft_delete_retention_days` (7 days in
dev/staging, 90 in prod) sets `blob_properties.delete_retention_policy` and
`container_delete_retention_policy` on the storage account — both scoped to Blob Storage. The
variable's own description says as much: "days a deleted **blob or container** remains
recoverable." `execution_state` is an `azurerm_storage_table`, a separate data plane within the
same account, and this module configures no table-level soft delete for it. A deleted or
overwritten row in `execution_state` is not recoverable through anything this tree turns on —
functionally the same position as AWS dev without PITR, except here it's true in every
environment including prod. Resume the execution rather than trying to repair its state, and
if durable recovery becomes a requirement, that's a module change (a table-level soft-delete or
export step), not an operational step available today.

**Stuck approval claim.** Same shape as AWS: `STALE_CLAIM_SECONDS` is an app-setting
environment variable with no backing Terraform variable
(`modules/approval/README.md`). Self-heals once the window passes; no manual step needed.

**One Azure-specific wrinkle.** If `create_model_key_secret = true`, the model API key's value
passes through Terraform state (see [SECRETS-ROTATION.md §3](SECRETS-ROTATION.md)). Restoring
Azure's Terraform state from a backup carries the same secret-retention consequence as the
original state file — treat a restored copy with the same access controls as the Key Vault,
and rotate the key if the backup's provenance is in question.

## GCP

**Execution state** (`google_firestore_database.state`, `modules/state`). Point-in-time
recovery is **off in dev, on in staging and prod**
(`enable_point_in_time_recovery`). As with AWS, restoring creates a **new** database — Firestore
database names are immutable, so this is a new resource, not an in-place repair:

```bash
gcloud firestore databases restore \
  --source-database=<name_prefix>-state \
  --snapshot-time=<RFC3339 timestamp> \
  --destination-database=<name_prefix>-state-restored \
  --project=<project_id>
```

`delete_protection_state` (on in prod) blocks `terraform destroy` from dropping the original
while you're deciding whether the restore is good — leave prod's protection on for the whole
recovery, not just as a matter of course.

**Stuck approval claim.** Unlike AWS and Azure, `stale_claim_seconds` **is** a Terraform
variable (`modules/approval/variables.tf`), wired to the executor's environment at plan time.
Changing the window is a `terraform apply`, not a manual function edit. It still self-heals
without intervention — the variable only matters if you want the default changed.

## Snowflake

**Execution state** (`snowflake_hybrid_table.execution_state`, schema `APP`). Protected by
**Time Travel**, retention **1 day in dev, 7 in staging, 30 in prod**
(`data_retention_time_in_days`, capped at 90 by the module's own variable validation).
Recovery is SQL, not a CLI restore:

```sql
-- inspect a past state without restoring anything
SELECT * FROM APP.EXECUTION_STATE AT(OFFSET => -3600);

-- undo a drop, within the retention window
UNDROP TABLE APP.EXECUTION_STATE;

-- clone the table as of a point in time, to inspect before overwriting the original
CREATE TABLE APP.EXECUTION_STATE_RESTORED CLONE APP.EXECUTION_STATE
  AT(TIMESTAMP => '2026-08-29 12:00:00'::TIMESTAMP_NTZ);
```

**Stuck approval claim.** `stale_claim_seconds` is a Terraform variable, same as GCP, but the
reclaim itself isn't a background sweep — it's a `WHERE` clause inside the `CLAIM_APPROVAL`
procedure (`CLAIMED_AT < DATEADD(second, -stale_claim_seconds, SYSDATE())`). A stale claim
isn't freed the moment the timer expires; it's freed the next time something calls that
procedure. If nothing is retrying, it sits stale until the next attempt.

**One Snowflake-specific wrinkle.** This tree's own Terraform state has no aspirational backend
scaffold at all — AWS, Azure, and GCP each carry a commented `backend` block in every
`envs/*/main.tf` as a sketch of where remote state would go; Snowflake's `envs/*/main.tf` has
none. Setting up remote state here for the first time starts from nothing, not from an
uncomment.

## Why the archive is out of scope

Every tree's `modules/archive` is built the opposite way from everything above: each supports a
locked retention policy — S3 Object Lock on AWS, an immutability policy on Azure, Bucket Lock
on GCP — off by default, and once locked, irreversible by design in every case. The point isn't
convenience recovery; it's that nobody, including an administrator, can quietly repair or erase
an entry once the lock is on. Evidence that can be fixed after the fact stops being evidence.
If you need something back from the archive, you're not undoing a loss — you're reading a
record that was never at risk of moving.

## Verify

```bash
test -f docs/HOW-TO-RECOVER.md
grep -q "AWS" docs/HOW-TO-RECOVER.md && grep -q "Azure" docs/HOW-TO-RECOVER.md \
  && grep -q "^## GCP" docs/HOW-TO-RECOVER.md && grep -q "^## Snowflake" docs/HOW-TO-RECOVER.md
grep -q "STALE_CLAIM_SECONDS\|stale_claim_seconds" docs/HOW-TO-RECOVER.md
grep -q "force-unlock" docs/HOW-TO-RECOVER.md
```
