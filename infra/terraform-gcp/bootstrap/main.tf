# Remote state bootstrap — the bucket the environment roots keep their state in.
#
# Every root under envs/ applies against a local state file until its `backend "gcs"` block
# is uncommented, and that block needs a bucket to point at. This root creates it. It is
# applied once per project, before any environment, and it is the one root whose own state
# stays local: a bucket cannot hold the state that records its own creation. Keep that
# local state file somewhere backed up, or re-import the bucket if it is lost — one
# resource, not the dozens an environment root would need.
#
# Nothing here is part of the agent. No module depends on it and the write boundary does
# not pass through it. It is a root of its own, not a module, so that an environment root
# can never destroy the bucket holding its own state.
#
# The GCS backend locks by default, so there is no lock table to create alongside it.

terraform {
  required_version = ">= 1.6"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 8.11"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.location
}

resource "google_storage_bucket" "state" {
  # Project ID in the name because bucket names are global.
  name     = "${var.project_id}-tfstate"
  location = var.location

  # IAM only, no object ACLs, and never public — even if a later policy binding tries.
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  # The recovery path. A corrupted or truncated state file is restored by reading back the
  # previous generation, which only exists if versioning was on before the bad write.
  versioning {
    enabled = true
  }

  # Old generations are the recovery path, not an archive. Keep a bounded number of them.
  lifecycle_rule {
    condition {
      num_newer_versions = var.state_versions_to_keep
      with_state         = "ARCHIVED"
    }
    action {
      type = "Delete"
    }
  }

  # State is the one thing in this project that cannot be rebuilt from the configuration.
  # `force_destroy = false` refuses to delete a bucket that still holds it, and removing
  # `prevent_destroy` is the deliberate act a `destroy` should require.
  force_destroy = false

  lifecycle {
    prevent_destroy = true
  }

  labels = {
    project    = var.project
    managed_by = "terraform"
    component  = "terraform-state"
  }
}
