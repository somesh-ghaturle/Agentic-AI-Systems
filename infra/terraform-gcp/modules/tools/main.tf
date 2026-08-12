# Tool layer — BUILDING-BLOCKS.md section 2
#
# The read/write split is the reason this module exists. From the doc:
#
#   "Read tools can be liberally available. Write tools go through validation and, for
#    high-impact actions, human approval. The model proposes writes; application code
#    decides whether they happen. That inversion is the single most important safety
#    property in the system."
#
# ---------------------------------------------------------------------------
# Why this module is closer to the AWS original than the Azure one
# ---------------------------------------------------------------------------
#
# On AWS the split is drawn by a Lambda resource policy: each function carries a statement
# naming who may invoke it, independent of what the caller's own policy permits.
#
# Azure has no equivalent for Functions, so terraform-azure/modules/tools substitutes an
# Entra app role, and terraform-azure/ARCHITECTURE.md section 2 is explicit that this leaves one
# load-bearing line where AWS has two independent locks.
#
# GCP has the resource policy. A Cloud Run service — which is what a gen2 function is
# underneath — carries its own IAM policy, and `roles/run.invoker` on that policy is
# exactly the AWS statement in different words. The bindings at the bottom of this file
# are the boundary, and they are enforced by the same subsystem that would have to be
# broken to bypass them.
#
# The second lock is an IAM Deny policy, and it lives in modules/orchestration rather than
# here, because it is a statement about the orchestrator rather than about any one tool.

terraform {
  required_version = ">= 1.6"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

locals {
  read_tools  = { for k, v in var.tools : k => v if v.access == "read" }
  write_tools = { for k, v in var.tools : k => v if v.access == "write" }

  # Cloud Run service names, and therefore function names, are lowercase with hyphens.
  # Tool names may carry underscores because they are also Python module names.
  service_names = { for k, v in var.tools : k => "${var.name_prefix}-tool-${replace(k, "_", "-")}" }
}

# ---------------------------------------------------------------------------
# Source packages
#
# Gen2 functions build from a GCS object rather than an inline upload, so the deployment
# package contract that AWS and Azure use — a local zip at `package_path` — is preserved
# by staging it here.
# ---------------------------------------------------------------------------

resource "google_storage_bucket" "source" {
  project = var.project_id

  name     = "${var.name_prefix}-tool-source"
  location = var.location

  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  # Source zips are build inputs, not evidence. Keeping every historical version costs
  # storage for no benefit once the function is deployed.
  versioning {
    enabled = false
  }

  dynamic "encryption" {
    for_each = var.kms_key_id == null ? [] : [var.kms_key_id]
    content {
      default_kms_key_name = encryption.value
    }
  }

  labels = var.labels
}

# The object name carries the package hash. Without it, uploading a changed zip under the
# same name leaves the deployed function untouched: Cloud Functions keys its build on the
# object path, so a same-named object is a no-op and the fix that was just deployed is not
# actually running.
resource "google_storage_bucket_object" "source" {
  for_each = var.tools

  name   = "${each.key}/${filemd5(each.value.package_path)}.zip"
  bucket = google_storage_bucket.source.name
  source = each.value.package_path
}

# ---------------------------------------------------------------------------
# The functions
# ---------------------------------------------------------------------------

resource "google_cloudfunctions2_function" "tool" {
  for_each = var.tools

  project  = var.project_id
  location = var.location

  name        = local.service_names[each.key]
  description = "Agentic tool ${each.key} (access: ${each.value.access})."

  build_config {
    runtime     = each.value.runtime
    entry_point = each.value.entry_point

    source {
      storage_source {
        bucket = google_storage_bucket.source.name
        object = google_storage_bucket_object.source[each.key].name
      }
    }
  }

  service_config {
    # "Timeout — every external call, no exceptions." A tool without one holds a worker
    # until something else breaks.
    timeout_seconds  = each.value.timeout_seconds
    available_memory = "${each.value.memory_mb}M"

    # Bound the concurrency of write tools specifically: agents retry, and an unbounded
    # retry storm against a write path is how a confused agent becomes an incident.
    max_instance_count = each.value.max_instances

    # Zero by default. A warm instance costs money continuously and buys latency that a
    # human-gated write path does not need.
    min_instance_count = each.value.min_instances

    service_account_email = var.tool_service_account_emails[each.key]

    environment_variables = merge(
      var.common_environment,
      each.value.environment,
      {
        TOOL_NAME   = each.key
        TOOL_ACCESS = each.value.access
      },
      var.trace_log_name == null ? {} : { TRACE_LOG_NAME = var.trace_log_name },
    )

    # Network reachability is not the boundary here — IAM is. `ALLOW_ALL` means the URL
    # resolves; it does not mean an unauthenticated caller gets past `run.invoker`.
    #
    # ALLOW_INTERNAL_ONLY is available and tempting, but it breaks invocation from
    # Workflows unless the call is routed through a VPC connector, and a network control
    # that forces a VPC into an otherwise serverless tree is a poor trade for defence in
    # depth that IAM already provides.
    ingress_settings               = var.ingress_settings
    all_traffic_on_latest_revision = true
  }

  labels = merge(var.labels, {
    component   = "tool-${replace(each.key, "_", "-")}"
    layer       = "tool"
    tool-access = each.value.access
  })
}

# ---------------------------------------------------------------------------
# The read/write invocation split — LOCK 1
#
# Read tools: the orchestrator invokes them directly.
# Write tools: ONLY the approval executor may invoke. The orchestrator can propose a
# write, but it cannot execute one — that is the inversion the architecture depends on.
#
# These are IAM policies on the underlying Cloud Run service. A gen2 function has no
# invoker binding of its own; granting `roles/cloudfunctions.invoker` on the function
# resource looks correct, appears in the console, and does not control HTTP invocation at
# all. That mistake is silent in the safe direction for read tools and silent in the
# dangerous direction for write tools, because the write tool would then be invokable by
# anyone holding run.invoker from another grant.
# ---------------------------------------------------------------------------

resource "google_cloud_run_service_iam_member" "read_tool_from_orchestrator" {
  for_each = local.read_tools

  project  = var.project_id
  location = var.location
  service  = google_cloudfunctions2_function.tool[each.key].name

  role   = "roles/run.invoker"
  member = var.orchestrator_member

  lifecycle {
    precondition {
      condition     = var.orchestrator_member != null
      error_message = "Read tools are declared but orchestrator_member is null, so nothing can invoke them. Supply the orchestrator's service account member string."
    }
  }
}

resource "google_cloud_run_service_iam_member" "write_tool_from_approval" {
  for_each = local.write_tools

  project  = var.project_id
  location = var.location
  service  = google_cloudfunctions2_function.tool[each.key].name

  role   = "roles/run.invoker"
  member = var.approval_executor_member

  lifecycle {
    precondition {
      condition     = var.approval_executor_member != null
      error_message = "Write tools are declared but approval_executor_member is null. A write tool with no approval gate in front of it means the model can execute irreversible actions directly — supply the approval module's executor member, or reclassify the tool as read."
    }
  }
}
