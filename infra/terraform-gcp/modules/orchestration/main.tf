# Orchestration — the workflow, and the second lock.
#
# The workflow definition lives in workflow.yaml.tftpl next to this file. It is a single
# template shared by dev and prod rather than a copy per environment: the AWS tree keeps
# one state-machine template per env root, and the two have drifted in small ways that are
# hard to see in review. The parameters that differ between environments — step ceiling,
# approval window — are variables here.

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
  workflow_name = "${var.name_prefix}-orchestrator"

  # Read tools only. Write tool URLs are not in this map at all, so the workflow has no
  # address to call even before IAM refuses it.
  #
  # This is the "shape" layer, and it is worth being clear that it is not a security
  # control: a URL is not a secret and Cloud Run URLs are derivable. It is here so that a
  # mistake has to be deliberate rather than incidental.
  retrieve_url = var.read_tool_urls["retrieve"]
  reason_url   = var.read_tool_urls["reason"]
}

resource "google_workflows_workflow" "orchestrator" {
  project = var.project_id
  region  = var.location

  name        = local.workflow_name
  description = "Agentic orchestrator. Read path direct; write path gated on a human resolving a callback."

  service_account = var.orchestrator_service_account_email

  # LOG_ALL_CALLS records every step transition. It is verbose and it is the difference
  # between diagnosing a stuck execution in minutes and reconstructing it from traces.
  call_log_level = var.call_log_level

  source_contents = templatefile("${path.module}/workflow.yaml.tftpl", {
    retrieve_url             = local.retrieve_url
    reason_url               = local.reason_url
    validator_url            = var.validator_url
    trace_emitter_url        = var.trace_emitter_url
    max_steps                = var.max_steps
    approval_timeout_seconds = var.approval_timeout_seconds
  })

  labels = var.labels

  lifecycle {
    precondition {
      condition     = can(var.read_tool_urls["retrieve"]) && can(var.read_tool_urls["reason"])
      error_message = "read_tool_urls must contain both \"retrieve\" and \"reason\". The workflow calls them by name; a missing key fails at plan time here rather than at the first execution."
    }

    precondition {
      condition     = var.trace_emitter_url != null
      error_message = "trace_emitter_url is null, so the orchestrator has nowhere to send its own records. The loop-bound and spend alerts would sit at zero forever, which is indistinguishable from a healthy system. Enable the trace emitter in modules/observability."
    }
  }
}

# Whoever starts executions. Not granted to any workload in this tree — the caller is
# outside it.
#
# ---------------------------------------------------------------------------
# This grant is coarser than its AWS and Azure counterparts, and not by choice
# ---------------------------------------------------------------------------
#
# The Workflows API supports a per-workflow IAM policy. The Terraform provider does not
# expose it: there is no `google_workflows_workflow_iam_member`, and there never has been
# — every other IAM-bearing resource in this tree has one, which makes the absence easy to
# assume away rather than notice.
#
# So this is a project-level binding. `roles/workflows.invoker` here lets the caller start
# *any* workflow in the project, not just this one. That is broader than the AWS tree's
# resource-scoped `states:StartExecution`.
#
# Two things keep the practical difference at zero:
#
#   1. This tree assumes one project per environment, and one orchestrator per
#      environment. The set "workflows in this project" and the set "this workflow" have
#      the same single member.
#   2. The caller is an external front door, not a workload — it holds no other grant in
#      this tree, and nothing else here holds workflows.invoker.
#
# Both of those are assumptions rather than enforced properties. If you add a second
# workflow to this project, this binding widens silently and nothing fails. To scope it
# properly, drop `caller_members` and bind out of band instead:
#
#   gcloud workflows add-iam-policy-binding NAME \
#     --location=REGION --member=MEMBER --role=roles/workflows.invoker
#
# which writes the per-workflow policy the provider cannot.
# ---------------------------------------------------------------------------

resource "google_project_iam_member" "workflow_invoker" {
  for_each = var.caller_members

  project = var.project_id
  role    = "roles/workflows.invoker"
  member  = each.value
}

# The workflow writes its own execution logs.
resource "google_project_iam_member" "orchestrator_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = var.orchestrator_member
}

# ---------------------------------------------------------------------------
# LOCK 2 — the IAM Deny policy
#
# modules/tools draws the boundary by granting run.invoker on write tools to the executor
# and to nobody else. That is the AWS resource-policy equivalent and it is the primary
# control.
#
# This is the second, independent lock: an explicit denial of the invoke permission to the
# orchestrator on those specific services. Deny rules are evaluated *before* allow
# policies, so this holds even if somebody later grants the orchestrator a broad
# run.invoker at project level — the exact accident that resource-scoped grants alone
# cannot prevent.
#
# Between them they reproduce the AWS property: remove either and the other still refuses.
# Azure has no equivalent of the second lock at all, which is why
# terraform-azure/ARCHITECTURE.md section 2 describes one lock and two mitigations.
#
# ---------------------------------------------------------------------------
# Two things about this that are worth knowing before relying on it
# ---------------------------------------------------------------------------
#
# 1. Not every IAM permission is supported in deny policies, and the supported set changes.
#    An unsupported permission string is rejected at apply time, not at plan time, so
#    `terraform validate` passing says nothing about whether this works.
#
# 2. A deny policy that names the wrong permission applies cleanly and denies nothing. It
#    appears in the console, it looks like a control, and the boundary rests entirely on
#    lock 1 without anything indicating so.
#
# Rehearse it once against a throwaway service account before trusting it: grant that
# account run.invoker on a write tool directly, confirm the deny still blocks the call,
# and confirm removing the deny unblocks it. A control nobody has seen refuse is a
# hypothesis, not a control. HOW-TO-DEPLOY.md has the commands.
# ---------------------------------------------------------------------------

resource "google_iam_deny_policy" "write_boundary" {
  count = length(var.write_tool_service_names) > 0 ? 1 : 0

  provider = google

  parent       = urlencode("cloudresourcemanager.googleapis.com/projects/${var.project_id}")
  name         = "${var.name_prefix}-write-boundary"
  display_name = "Deny the orchestrator invoke on write tools"

  rules {
    deny_rule {
      # Deny policies take principals in `principal://` form, not the `serviceAccount:`
      # form every other IAM resource uses. Passing the allow-policy form is accepted and
      # matches nothing.
      denied_principals = [
        "principal://iam.googleapis.com/projects/-/serviceAccounts/${var.orchestrator_service_account_email}"
      ]

      denied_permissions = var.denied_invoke_permissions

      denial_condition {
        title       = "write tools only"
        description = "Scopes the denial to write tool services, so the orchestrator keeps its access to read tools, the validator, and the trace emitter."
        expression  = join(" || ", [for name in var.write_tool_service_names : "resource.name.endsWith(\"/${name}\")"])
      }
    }
  }
}
