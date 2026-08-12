# Identity layer.
#
# One service account per workload. The alternative — a shared account — makes every grant
# in this stack a grant to everything, which is precisely what the read/write split exists
# to prevent.
#
# This module exists for the same reason the Azure `identity` module does: to break a
# dependency cycle. modules/tools needs the executor's identity to scope the write-tool
# invoker binding; modules/approval needs the write tools' addresses to call them. On AWS
# that cycle is broken by computing ARNs in `locals`, because ARNs are deterministic.
#
# GCP service account emails are deterministic too — `${account_id}@${project}.iam
# .gserviceaccount.com` — so the AWS trick would work here. It is deliberately not used.
# Constructing an email string produces a value that is correct but unverified: if the
# account is never created, or is created in another project, Terraform is perfectly happy
# and the IAM binding silently references a principal that does not exist. GCP accepts
# bindings to nonexistent service accounts without error.
#
# Creating them here and passing the resource through means a typo is a plan-time failure
# rather than a runtime 403 that looks like a permissions bug.

terraform {
  required_version = ">= 1.6"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

resource "google_service_account" "workload" {
  for_each = var.identities

  project = var.project_id

  # Account IDs are 6-30 characters, lowercase alphanumeric and hyphens, and must start
  # with a letter. Tool names may carry underscores (they are also Python module names),
  # so the caller is expected to have normalized them already. The validation on
  # `var.identities` fails loudly rather than letting the API reject a half-finished apply.
  account_id   = each.value
  display_name = "${var.name_prefix} ${each.value}"

  description = "Agentic system workload identity: ${each.value}. One principal per workload; see modules/identity for why these are not shared."
}
