# Archive — the evidence bucket.
#
# Traces land here and, in prod, cannot be removed by anyone. That is the whole point: an
# audit trail an operator can quietly trim is not an audit trail.
#
# GCS Bucket Lock is the closest thing GCP has to S3 Object Lock in COMPLIANCE mode, and
# it is closer than Azure's immutability policy. Once `is_locked = true` is applied:
#
#   - the retention period can be increased, never decreased or removed
#   - objects cannot be deleted or overwritten until they reach the retention age
#   - the bucket cannot be deleted while it holds any object still under retention
#   - no principal can override this, including project owners and Google support
#
# The last point is what makes it worth using and what makes it dangerous. Locking is
# irreversible. A bucket locked with a ten-year retention is a ten-year commitment to
# paying for that storage, and there is no support ticket that undoes it.
#
# So dev does not lock, and the variable that controls it has no default — the caller
# states the intent explicitly rather than inheriting a commitment.

terraform {
  required_version = ">= 1.6"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.44"
    }
  }
}

resource "google_storage_bucket" "archive" {
  project = var.project_id

  name     = "${var.name_prefix}-archive"
  location = var.location

  storage_class = "STANDARD"

  # Uniform access means IAM alone decides who can read this, with no per-object ACLs
  # shadowing it. Legacy ACLs are how a bucket ends up readable by principals who appear
  # nowhere in its IAM policy.
  uniform_bucket_level_access = true

  # Belt and braces against the classic misconfiguration. `enforced` means the bucket
  # cannot be made public even by someone who intends to.
  public_access_prevention = "enforced"

  # Retain non-current versions so an overwrite is recoverable. Under a locked retention
  # policy an overwrite is impossible anyway, but dev is not locked and this is where the
  # accident happens.
  versioning {
    enabled = true
  }

  dynamic "encryption" {
    for_each = var.kms_key_id == null ? [] : [var.kms_key_id]
    content {
      default_kms_key_name = encryption.value
    }
  }

  # Age out to colder classes. Under a locked retention policy these transitions are still
  # permitted — Bucket Lock prevents deletion and modification, not storage class changes.
  dynamic "lifecycle_rule" {
    for_each = var.transition_nearline_days == null ? [] : [var.transition_nearline_days]
    content {
      condition {
        age = lifecycle_rule.value
      }
      action {
        type          = "SetStorageClass"
        storage_class = "NEARLINE"
      }
    }
  }

  dynamic "lifecycle_rule" {
    for_each = var.transition_coldline_days == null ? [] : [var.transition_coldline_days]
    content {
      condition {
        age = lifecycle_rule.value
      }
      action {
        type          = "SetStorageClass"
        storage_class = "COLDLINE"
      }
    }
  }

  # Deletion, for environments that want it. A delete rule and a retention policy can
  # coexist, but the delete only takes effect once the object is past retention — GCS
  # enforces the retention policy first. Setting expiration_days shorter than the
  # retention period is therefore not an error and not a shortcut; the objects simply sit
  # there until retention lets them go.
  dynamic "lifecycle_rule" {
    for_each = var.expiration_days == null ? [] : [var.expiration_days]
    content {
      condition {
        age = lifecycle_rule.value
      }
      action {
        type = "Delete"
      }
    }
  }

  # The WORM window. Null means no retention policy at all, which is what dev wants.
  dynamic "retention_policy" {
    for_each = var.retention_days == null ? [] : [var.retention_days]
    content {
      retention_period = retention_policy.value * 24 * 60 * 60

      # Irreversible. See the header. Terraform will apply this without ceremony and there
      # is no undo, which is why `lock_retention_policy` has no default.
      is_locked = var.lock_retention_policy
    }
  }

  labels = var.labels

  lifecycle {
    precondition {
      condition     = var.lock_retention_policy == false || var.retention_days != null
      error_message = "lock_retention_policy is true but retention_days is null. Locking without a retention period locks nothing — set retention_days, or set lock_retention_policy to false."
    }
  }
}

# Writers append; they do not get delete. Under a locked policy the distinction is
# academic for objects under retention, but it holds in dev too, where the policy is off
# and roles/storage.objectAdmin would let a trace emitter erase its own history.
resource "google_storage_bucket_iam_member" "writer" {
  for_each = var.writer_members

  bucket = google_storage_bucket.archive.name
  role   = "roles/storage.objectCreator"
  member = each.value
}

resource "google_storage_bucket_iam_member" "reader" {
  for_each = var.reader_members

  bucket = google_storage_bucket.archive.name
  role   = "roles/storage.objectViewer"
  member = each.value
}
