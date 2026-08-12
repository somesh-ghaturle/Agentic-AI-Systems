# Security layer — the customer-managed encryption key.
#
# One key ring, one key, used by every service in the stack that holds anything worth
# encrypting: Pub/Sub messages, the archive bucket, the function source bucket, and the
# log bucket.
#
# The load-bearing part of this module is not the key. It is the service-agent grants
# below. On GCP a customer-managed key is used by the *service*, not by your workload
# identity: Pub/Sub encrypts with the Pub/Sub service agent, Cloud Storage with the
# Storage service agent. Forget one grant and the resource that needs it fails to create
# with a message about the key being unavailable — or worse, for Pub/Sub, publishes start
# failing later rather than at apply time.
#
# This is the GCP analogue of the AWS key-policy trap documented in
# terraform-aws/modules/security: there the key policy has to admit `sns.amazonaws.com`
# or approval messages publish successfully and are never delivered.

terraform {
  required_version = ">= 1.6"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

data "google_project" "current" {
  project_id = var.project_id
}

resource "google_kms_key_ring" "main" {
  project = var.project_id

  name     = "${var.name_prefix}-keyring"
  location = var.location
}

resource "google_kms_crypto_key" "main" {
  name     = "${var.name_prefix}-key"
  key_ring = google_kms_key_ring.main.id

  purpose         = "ENCRYPT_DECRYPT"
  rotation_period = var.rotation_period

  version_template {
    algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
    protection_level = var.protection_level
  }

  labels = var.labels

  # A key ring cannot be deleted, and neither can a key — GCP only lets you destroy key
  # *versions*. Terraform will happily drop this from state on destroy and leave the key
  # behind, which is fine for the archive (see modules/archive) but surprising the first
  # time. Prod sets this to true so a `terraform destroy` cannot orphan a key that data
  # still depends on.
  lifecycle {
    prevent_destroy = false
  }
}

# ---------------------------------------------------------------------------
# Service agent grants
#
# Each of these is a different Google-managed principal. They are not interchangeable, and
# a missing one fails at a different point in the apply depending on the service.
# ---------------------------------------------------------------------------

locals {
  project_number = data.google_project.current.number

  # The service agents that need to encrypt with this key. Keyed so that removing a
  # consumer removes exactly one binding rather than reshuffling a list.
  service_agents = {
    pubsub  = "serviceAccount:service-${local.project_number}@gcp-sa-pubsub.iam.gserviceaccount.com"
    storage = "serviceAccount:service-${local.project_number}@gs-project-accounts.iam.gserviceaccount.com"
    logging = "serviceAccount:service-${local.project_number}@gcp-sa-logging.iam.gserviceaccount.com"
    run     = "serviceAccount:service-${local.project_number}@serverless-robot-prod.iam.gserviceaccount.com"
  }
}

resource "google_kms_crypto_key_iam_member" "service_agent" {
  for_each = local.service_agents

  crypto_key_id = google_kms_crypto_key.main.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = each.value
}

# Workload identities that read secrets or decrypt payloads directly. Distinct from the
# service agents above: those encrypt on behalf of a service, these decrypt in handler
# code.
resource "google_kms_crypto_key_iam_member" "workload" {
  for_each = var.decrypter_members

  crypto_key_id = google_kms_crypto_key.main.id
  role          = "roles/cloudkms.cryptoKeyDecrypter"
  member        = each.value
}

# ---------------------------------------------------------------------------
# Secret Manager — the model API key, when one is needed
#
# Claude on Vertex AI authenticates with the caller's own service account, so there is
# usually no key to hold. This exists for the case where a handler calls a model outside
# Vertex AI, and it is off by default rather than creating an empty secret nobody fills.
# ---------------------------------------------------------------------------

resource "google_secret_manager_secret" "model_key" {
  count = var.create_model_key_secret ? 1 : 0

  project   = var.project_id
  secret_id = "${var.name_prefix}-model-api-key"

  replication {
    user_managed {
      replicas {
        location = var.location

        customer_managed_encryption {
          kms_key_name = google_kms_crypto_key.main.id
        }
      }
    }
  }

  labels = var.labels
}

resource "google_secret_manager_secret_iam_member" "model_key_reader" {
  for_each = var.create_model_key_secret ? var.secret_reader_members : {}

  project   = var.project_id
  secret_id = google_secret_manager_secret.model_key[0].secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = each.value
}
