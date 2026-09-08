variable "project" {
  description = <<-EOT
    Project name. Combined with the environment to prefix every resource.

    The length limit is tighter here than on AWS or Azure, and tighter in this root than in
    envs/dev or envs/prod. The reason is service account IDs: they cap at 30 characters, and
    modules/identity refuses anything longer rather than letting the API reject a
    half-finished apply. The IDs this root derives are "<project>-staging-<tool name with
    hyphens>", and `process_refund` normalizes to a 14-character suffix.

    "staging" is three characters longer than "prod", so this root allows 7 where envs/prod
    allows 10. A project name that is valid in prod can therefore be invalid here — which is
    the opposite of the usual direction, and worth knowing before you copy prod's tfvars.
    Shorten the project rather than reaching for truncation: two truncated IDs that collide
    produce one service account shared by two tools, quietly undoing the
    one-identity-per-workload property.
  EOT

  type = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,6}$", var.project))
    error_message = "project must be 3-7 characters, start with a lowercase letter, and contain only lowercase letters, digits and hyphens. The ceiling is the 30-character service account ID limit, and \"staging\" spends three more of them than \"prod\" — see the description."
  }
}

variable "project_id" {
  description = "GCP project ID this environment deploys into. Distinct from `project`, which is only a naming prefix. Give staging its own project: the Vertex AI floor setting this root enables is enforced on every caller in the project, so a shared project would apply staging's blocking guardrail to another environment's traffic."
  type        = string
}

variable "region" {
  description = "Region for regional resources — functions, workflow, KMS, buckets, Vector Search. Use prod's: region determines which machine types and model versions exist, so a rehearsal elsewhere can pass on capacity prod does not have."
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
  description = "Vertex AI model identifier the reason handler requests. Match prod exactly — a rehearsal against a different model measures a different system. Nothing here validates that it exists or that Model Garden terms have been accepted for it; see HOW-TO-DEPLOY.md."
  type        = string
  default     = "claude-opus-5"
}

# ---------------------------------------------------------------------------
# Cost controls
#
# Vector Search is the largest standing cost in this tree, because a deployed index has no
# scale-to-zero — the minimum replica count is a continuous bill rather than a ceiling.
# ---------------------------------------------------------------------------

variable "knowledge_min_replicas" {
  description = "Minimum Vector Search replicas. One, where prod runs two. The second replica keeps retrieval available while a replica restarts, which is durability rather than behaviour — a rehearsal cannot observe the difference, and it doubles the standing bill."
  type        = number
  default     = 1
}

variable "knowledge_max_replicas" {
  description = "Maximum Vector Search replicas. Must exceed knowledge_min_replicas: whether the index scales out at all is behaviour, and an environment pinned at 1/1 never exercises it. Below prod's five because staging load is a rehearsal."
  type        = number
  default     = 3

  # Checked against the constant rather than against knowledge_min_replicas, because a
  # validation rule that reads another variable requires Terraform 1.9 and every root in
  # this tree declares `required_version = ">= 1.6"`. Raising the floor for one convenience
  # check would break a consumer this repository tells to expect 1.6. If you raise the
  # minimum above 1, raise this too — nothing here can check that for you.
  validation {
    condition     = var.knowledge_max_replicas > 1
    error_message = "max must be at least 2 and must exceed knowledge_min_replicas. Pinning them equal disables autoscaling, so prod's scale-out path is never exercised before prod runs it."
  }
}

variable "daily_cost_threshold_usd" {
  description = "Daily spend, in USD, above which the cost alert fires. Lower than prod's 500 because staging load is a rehearsal — a day that costs this much here is a runaway loop rather than growth."
  type        = number
  default     = 50

  validation {
    condition     = var.daily_cost_threshold_usd > 0
    error_message = "daily_cost_threshold_usd must be positive."
  }
}

# ---------------------------------------------------------------------------
# Retention
# ---------------------------------------------------------------------------

variable "archive_expiration_days" {
  description = "Days before archived traces are deleted. Prod sets this to null and locks a seven-year retention policy instead, because its archive is evidence. Staging's is the output of a rehearsal, so expiry is finite and required — an environment rebuilt every release must not accumulate an archive nothing removes."
  type        = number
  default     = 90

  # nullable = false rather than a null check in the condition below: prod accepts null and
  # means "retain indefinitely", so null is the value most likely to be copied across from
  # prod's tfvars, and it should be refused by the type system rather than by a rule that
  # has to evaluate `null > 0`.
  nullable = false

  validation {
    condition     = var.archive_expiration_days > 0
    error_message = "staging must expire its trace archive. Indefinite retention is a prod decision made from a records policy; staging has no such policy and no reader for old traces."
  }
}

# Deliberately absent: retention_days and lock_retention_policy.
#
# Prod sets both, committing its archive bucket for seven years. They are not exposed here
# because a locked retention policy cannot be shortened or removed by any principal —
# including the project owner and Google support — and the bucket cannot be deleted while
# anything is still under retention. A single tfvars line would permanently strand the
# storage of the one environment whose value depends on being destroyable.
# modules/archive receives null and false in main.tf.
#
# Also deliberately absent: any switch for Firestore delete protection. It is milder and
# reversible, but it makes Terraform abandon rather than destroy both databases, so a
# teardown leaves them behind for the next apply to collide with.

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

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
  description = "Validator package — deterministic ownership, permission, and limit checks that run before a human sees a proposal. Give it prod's policy limits: a validator that approves in staging what it would reject in prod turns the rehearsal into a false pass."

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
    zero alert is indistinguishable from a healthy system. That is precisely the defect
    staging is supposed to catch before prod inherits it, so supply it here.
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

    Point this at a staging approver group rather than the prod rotation. Whether approvals
    reach a human is part of what a rehearsal verifies, but rehearsing against the real
    rotation trains those people to click through prompts that do not matter.

    Empty means nobody can approve anything: every gated action sits until its window
    closes and is recorded as abandoned, which in a staging run reads as a gate defect.
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
  description = "Email addresses notified when an alert fires, keyed by name. Send these to a staging channel: alert routing is worth rehearsing, but paging the prod on-call for a rehearsal is how people learn to ignore the alert. Empty means the alert policies exist and notify nobody."
  type        = map(string)
  default     = {}
}

variable "vpc_connector" {
  description = "Serverless VPC Access connector for the handlers, by name or self-link. Null — the default — keeps this tree free of a VPC, which is the posture recorded in modules/knowledge for the index endpoint."
  type        = string
  default     = null
}
