variable "project" {
  description = <<-EOT
    Project name. Combined with the environment to prefix every resource.

    The length limit is tighter here than on AWS or Azure, and the reason is service
    account IDs: they cap at 30 characters, and modules/identity refuses anything longer
    rather than letting the API reject a half-finished apply. The IDs this root derives are
    "<project>-<env>-<tool name with hyphens>", so a 10-character project plus the longest
    environment name leaves exactly 14 characters for the longest tool name.
    `process_refund` is exactly 14, which is not a coincidence.

    The limit is set by prod rather than by dev — "prod" is a character longer than "dev" —
    and it is identical in both roots on purpose. A project name that fits in dev and not
    in prod is a failure discovered at the worst moment.

    If you need a longer tool name, shorten the project rather than reaching for
    truncation: two truncated IDs that collide produce one service account shared by two
    tools, which quietly undoes the one-identity-per-workload property.
  EOT

  type = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,9}$", var.project))
    error_message = "project must be 3-10 characters, start with a lowercase letter, and contain only lowercase letters, digits and hyphens. The ceiling is the 30-character service account ID limit — see the description."
  }
}

variable "project_id" {
  description = "GCP project ID this environment deploys into. Distinct from `project`, which is only a naming prefix. Separate projects per environment is the GCP idiom and this tree assumes it — see the note in main.tf about what breaks if dev and prod share one."
  type        = string
}

variable "region" {
  description = "Region for regional resources — functions, workflow, KMS, buckets, Vector Search. KMS keys can only encrypt resources co-located with them, so this is one value rather than several on purpose."
  type        = string
  default     = "us-central1"
}

variable "firestore_location" {
  description = "Firestore location. A region like `us-central1` or a multi-region like `nam5`. Immutable after creation — changing it later means a new database and a data migration."
  type        = string
  default     = "nam5"
}

variable "vertex_location" {
  description = "Vertex AI region for Claude model calls. Anthropic model availability varies by region and does not always include the region everything else runs in; us-east5 and europe-west1 carry the broadest selection."
  type        = string
  default     = "us-east5"
}

variable "model_id" {
  description = "Vertex AI model identifier the reason handler requests. Nothing here validates that it exists or that Model Garden terms have been accepted for it — see HOW-TO-DEPLOY.md."
  type        = string
  default     = "claude-opus-4-5@20251101"
}

variable "tools" {
  description = <<-EOT
    Tool definitions. See modules/tools/variables.tf for the full contract.

    The `access` field decides who may invoke each function — "read" means the orchestrator
    calls it directly, "write" means only the approval executor can. Classify by what the
    handler DOES, not by what it is called: a tool named "lookup_account" that also writes
    an audit row is a write tool, and no amount of Terraform can detect otherwise.
  EOT

  type = map(object({
    access          = string
    entry_point     = string
    runtime         = string
    package_path    = string
    timeout_seconds = number
    max_instances   = number
    memory_mb       = optional(number, 512)
    min_instances   = optional(number, 0)
    environment     = optional(map(string), {})
  }))

  default = {}
}

variable "approval_validator" {
  description = "Validator package — deterministic ownership, permission, and limit checks that run before a human sees a proposal."

  type = object({
    package_path = string
    runtime      = optional(string, "python312")
    entry_point  = optional(string, "handler")
    environment  = optional(map(string), {})
  })
}

variable "approval_executor" {
  description = "Executor package — the only principal permitted to invoke write tools."

  type = object({
    package_path = string
    runtime      = optional(string, "python312")
    entry_point  = optional(string, "handler")
    environment  = optional(map(string), {})
  })
}

variable "trace_emitter" {
  description = <<-EOT
    The function the orchestrator calls to write its own trace records. Source:
    ../../../terraform-aws/src/emit_trace, ported to the Cloud Logging API.

    Null is accepted by modules/observability and rejected by modules/orchestration, which
    is deliberate: without it the loop-bound and spend alerts sit at zero forever, and a
    zero alert is indistinguishable from a healthy system.
  EOT

  type = object({
    package_path = string
    runtime      = optional(string, "python312")
    entry_point  = optional(string, "handler")
  })
}

variable "approver_members" {
  description = <<-EOT
    Principals permitted to resolve approvals, keyed by name. Member strings —
    `user:someone@example.com`, `group:approvers@example.com`.

    Empty means nobody can approve anything. Safe, and also a system where every gated
    action sits until its window closes, which is worth noticing rather than discovering.
  EOT

  type    = map(string)
  default = {}
}

variable "caller_members" {
  description = "Principals granted workflows.invoker — whoever starts executions. No workload in this tree holds it; the caller lives outside these modules."
  type        = map(string)
  default     = {}
}

variable "alert_email_receivers" {
  description = "Email addresses notified when an alert fires, keyed by name. Empty means the alert policies exist and notify nobody."
  type        = map(string)
  default     = {}
}
