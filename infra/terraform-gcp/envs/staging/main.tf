# Staging environment.
#
# Structurally identical to envs/dev and envs/prod. Every difference is a variable value,
# and each one below is annotated with what it costs and what it buys. Diff this file
# against envs/prod/main.tf: the module blocks, their order, and their wiring should be
# the same line for line, and anything else is drift worth explaining.
#
# What staging is FOR, since "between dev and prod" does not say much on its own: the
# dev/prod difference in this tree is not scale, it is posture. Dev runs without a Vertex
# AI floor setting, with call arguments in the workflow log, and with loose alert
# thresholds. Those are exactly the settings whose first real exercise would otherwise be
# the first prod apply.
#
# The floor setting is the one worth naming twice. It is enforced by Vertex AI on every
# generateContent in the project, so turning it on for the first time in prod means the
# first thing it ever blocks is a production request. Here it blocks a rehearsal instead.
#
# The rule for what staging takes from where:
#
#   From prod — every REVERSIBLE control
#     Vertex floor setting    on, and blocking rather than inspect-only
#     Workflow call logging    LOG_ERRORS_ONLY — arguments stay out of the log
#     Alert thresholds         prod's, not dev's
#     Firestore PITR           on, both databases
#     Step and approval budgets  prod's
#
#   From dev — everything IRREVERSIBLE, plus pure durability
#     Archive retention lock   never — see below
#     Delete protection        off, on both databases
#     KMS protection level     SOFTWARE, not HSM
#     Vector Search replicas   1 minimum, not prod's 2
#     Retention                archive expires at 90 days
#
# ---------------------------------------------------------------------------
# The two settings that would make this environment permanent
#
# `lock_retention_policy = true` on the archive is irreversible in the strongest sense
# available on GCP: no principal — not the project owner, not Google support — can shorten
# the period or delete an object before it ages out, and the bucket cannot be deleted while
# anything is still under retention. Prod accepts a 7-year commitment because its archive
# is evidence. Staging's is the output of a rehearsal, so it stays unlocked, and the
# setting is not exposed as a variable here.
#
# `enable_delete_protection` is milder and pulls the same direction: it makes Terraform
# abandon rather than destroy the Firestore databases, so a teardown leaves them behind and
# the next apply collides with them. Prod wants exactly that. An environment rebuilt every
# release does not.
#
# ---------------------------------------------------------------------------
# One project per environment
#
# This root assumes staging lives in its own GCP project, for the same reasons envs/prod
# gives: `roles/datastore.user` covers every Firestore database in the project, service
# account IDs are unique per project, and an IAM Deny policy attaches to the project rather
# than to a resource. It matters more here than between any other pair, because the Vertex
# AI floor setting below applies to every caller in the project — sharing a project with
# dev would apply staging's blocking guardrail to dev's traffic.
#
# ---------------------------------------------------------------------------
# Two dependency cycles, and how each is broken
#
# See envs/prod/main.tf. The reasoning is identical and is not repeated.
# ---------------------------------------------------------------------------

terraform {
  required_version = ">= 1.6"

  # Remote state with locking. GCS backends lock by default — there is no separate lock
  # table to forget. Staging is shared by definition: it is where more than one person
  # verifies a release, so local state has the same problem here it has in prod.
  #
  # backend "gcs" {
  #   bucket = "<your-tf-state-bucket>"
  #   prefix = "agentic/staging"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region

  default_labels = local.labels
}

locals {
  env         = "staging"
  name_prefix = "${var.project}-${local.env}"

  # --- cycle-breakers ------------------------------------------------------
  workflow_name       = "${local.name_prefix}-orchestrator"
  archive_bucket_name = "${local.name_prefix}-archive"

  # --- service account IDs -------------------------------------------------
  #
  # Capped at 30 characters by the API. "staging" is three characters longer than "prod",
  # which is why var.project is validated to 7 here rather than prod's 10 — see the note
  # in variables.tf.
  tool_sa_ids = { for k, v in var.tools : k => "${local.name_prefix}-${replace(k, "_", "-")}" }

  fixed_sa_ids = {
    orchestrator  = "${local.name_prefix}-orchestrator"
    validator     = "${local.name_prefix}-approval-val"
    executor      = "${local.name_prefix}-approval-exec"
    trace_emitter = "${local.name_prefix}-trace-emitter"
  }

  sa_ids = merge(local.tool_sa_ids, local.fixed_sa_ids)

  tool_members = { for k, id in local.tool_sa_ids : k => module.identity.members[id] }
  tool_emails  = { for k, id in local.tool_sa_ids : k => module.identity.emails[id] }

  orchestrator_member = module.identity.members[local.fixed_sa_ids.orchestrator]
  orchestrator_email  = module.identity.emails[local.fixed_sa_ids.orchestrator]
  validator_member    = module.identity.members[local.fixed_sa_ids.validator]
  validator_email     = module.identity.emails[local.fixed_sa_ids.validator]
  executor_member     = module.identity.members[local.fixed_sa_ids.executor]
  executor_email      = module.identity.emails[local.fixed_sa_ids.executor]
  emitter_member      = module.identity.members[local.fixed_sa_ids.trace_emitter]
  emitter_email       = module.identity.emails[local.fixed_sa_ids.trace_emitter]

  labels = {
    project     = var.project
    environment = local.env
    managed-by  = "terraform"
    component   = "agentic-system"
  }
}

# ---------------------------------------------------------------------------
# Identity — created first, depends on nothing.
# ---------------------------------------------------------------------------

module "identity" {
  source = "../../modules/identity"

  project_id  = var.project_id
  name_prefix = local.name_prefix
  identities  = toset(values(local.sa_ids))
}

module "security" {
  source = "../../modules/security"

  project_id  = var.project_id
  name_prefix = local.name_prefix

  # Must be the same region as everything it encrypts.
  location = var.region

  # SOFTWARE, where prod uses HSM. HSM costs meaningfully more per key version and per
  # cryptographic operation, and what it buys is a key that never exists in software form —
  # a property that matters because prod's archive is evidence. Staging's is not, and the
  # API surface is identical either way, so a rehearsal cannot tell the difference.
  protection_level = "SOFTWARE"

  decrypter_members = {}

  # Claude on Vertex AI authenticates as the caller's service account, so there is no key
  # to store. See modules/model-integration.
  create_model_key_secret = false

  labels = local.labels
}

module "state" {
  source = "../../modules/state"

  project_id  = var.project_id
  name_prefix = local.name_prefix
  location    = var.firestore_location

  # On, as in prod. PITR changes the database's billing and backup behaviour, so leaving it
  # off would mean prod runs a configuration staging never exercised.
  enable_point_in_time_recovery = true

  # Off, where prod has it on. Delete protection makes Terraform abandon rather than
  # destroy the database, so a `terraform destroy` leaves it behind and the next apply
  # collides with what was left. Prod wants that. An environment rebuilt every release
  # cannot afford it.
  enable_delete_protection = false

  # Tools only. The validator and executor also need datastore.user, and modules/approval
  # grants it to them — `roles/datastore.user` is project-level, so granting it here as
  # well would create two Terraform resources managing the same IAM membership.
  datastore_user_members = local.tool_members
}

module "archive" {
  source = "../../modules/archive"

  project_id  = var.project_id
  name_prefix = local.name_prefix
  location    = var.region
  kms_key_id  = module.security.kms_key_id

  # ---------------------------------------------------------------------------
  # No retention lock, and deliberately not a variable — see variables.tf.
  #
  # Prod locks seven years of retention here and thereby commits the bucket for seven
  # years. Exposing that as a tfvars line in staging would let one edit permanently strand
  # the storage of the one environment whose value depends on being destroyable.
  # ---------------------------------------------------------------------------
  retention_days        = null
  lock_retention_policy = false

  # Dev's lifecycle. Staging traces are a rehearsal's output; the next release replaces
  # them. Unlike prod, expiry is finite and set — an environment rebuilt every release must
  # not accumulate an archive nothing removes.
  transition_nearline_days = 7
  transition_coldline_days = 30
  expiration_days          = var.archive_expiration_days

  # The log sink's own service account, not a workload. Until it holds objectCreator the
  # sink exists, reports no error, and delivers nothing.
  writer_members = {
    trace_sink = module.observability.sink_writer_identity
  }

  labels = local.labels
}

module "knowledge" {
  source = "../../modules/knowledge"

  project_id  = var.project_id
  name_prefix = local.name_prefix
  location    = var.region
  kms_key_id  = module.security.kms_key_id

  # Must match the embedding model the retrieve handler uses. 768 is text-embedding-004.
  # A mismatch is accepted at index-create time and fails on every query afterwards.
  dimensions = 768

  # One replica minimum, where prod runs two. A deployed index has no scale-to-zero, so
  # min_replica_count is a continuous bill rather than a ceiling, and it is the largest
  # standing cost in this tree. The second replica buys availability during a replica
  # restart — durability, not behaviour, and not something a rehearsal observes.
  #
  # max_replica_count stays above the minimum on purpose: whether the index scales out at
  # all is behaviour, and an environment pinned at 1/1 never exercises it.
  machine_type      = "e2-standard-2"
  min_replica_count = var.knowledge_min_replicas
  max_replica_count = var.knowledge_max_replicas

  # The retrieve tool's identity, not the orchestrator's.
  querier_members = {
    retrieve = local.tool_members["retrieve"]
  }

  labels = local.labels
}

module "model_integration" {
  source = "../../modules/model-integration"

  project_id = var.project_id

  # Not var.region. Anthropic model availability on Vertex AI is region-specific and does
  # not always include the region the rest of the stack runs in.
  location = var.vertex_location
  model_id = var.model_id

  manage_api_enablement = true

  # The reason handler, and nothing else.
  model_caller_members = {
    reason = local.tool_members["reason"]
  }

  # ---------------------------------------------------------------------------
  # The guardrail, at prod's settings — including the two dev leaves off.
  # ---------------------------------------------------------------------------

  name_prefix      = local.name_prefix
  create_guardrail = true

  jailbreak_confidence_level = "LOW_AND_ABOVE"
  sdp_mode                   = "basic"

  # On, where dev leaves it off, and the single most valuable thing this environment
  # verifies about the model layer. A floor setting is enforced by Vertex AI on every
  # generateContent in the project, so enabling it for the first time in prod means the
  # first request it ever blocks is a real one. It also reaches every Vertex AI caller in
  # the project, which is why staging wants its own project.
  create_floor_setting = true

  # Blocking, not inspect-only — again matching prod. A floor setting in inspect-only mode
  # appears in the console, reads as enabled, and stops nothing, so rehearsing against
  # inspect-only would verify the console rather than the control.
  floor_setting_block = true

  labels = local.labels
}

module "observability" {
  source = "../../modules/observability"

  project_id  = var.project_id
  name_prefix = local.name_prefix
  location    = var.region

  # The orchestrator's own records reach the log-based metrics only through this function.
  # Omit it and the loop-bound and spend alerts sit at zero forever, which reads exactly
  # like a healthy system — the failure mode staging exists to catch before prod inherits.
  trace_emitter = {
    package_path          = var.trace_emitter.package_path
    runtime               = var.trace_emitter.runtime
    entry_point           = var.trace_emitter.entry_point
    service_account_email = local.emitter_email
    member                = local.emitter_member
    orchestrator_member   = local.orchestrator_member
  }

  # Every handler that emits a trace. The orchestrator and the emitter are absent on
  # purpose — see envs/prod/main.tf.
  trace_writer_members = merge(local.tool_members, {
    validator = local.validator_member
    executor  = local.executor_member
  })

  alert_email_receivers = var.alert_email_receivers

  # Lower than prod's 500. Staging load is a rehearsal, so a day that costs this much here
  # is a runaway loop rather than growth.
  daily_cost_threshold_usd = var.daily_cost_threshold_usd

  # Prod's thresholds, not dev's. A sustained trace-schema failure rate means the emitter
  # and the metric filters disagree about the record shape — a disagreement that is silent,
  # because the alerts simply match nothing. Staging is where it should surface.
  schema_failure_threshold     = 3
  abandoned_approval_threshold = 1

  # Deterministic — see the cycle note in envs/prod/main.tf.
  workflow_name = local.workflow_name

  archive_bucket_name = local.archive_bucket_name

  labels = local.labels
}

# ---------------------------------------------------------------------------
# The tool layer.
#
# Read tools are invoked by the orchestrator; write tools only by the approval executor.
# That split is enforced in the module by Cloud Run IAM, not by convention here.
# ---------------------------------------------------------------------------

module "tools" {
  source = "../../modules/tools"

  project_id  = var.project_id
  name_prefix = local.name_prefix
  location    = var.region
  kms_key_id  = module.security.kms_key_id

  tools = var.tools

  tool_service_account_emails = local.tool_emails

  orchestrator_member      = local.orchestrator_member
  approval_executor_member = local.executor_member

  trace_log_name = module.observability.trace_log_name

  common_environment = {
    GCP_PROJECT     = var.project_id
    EXECUTIONS_DB   = module.state.database_name
    EXECUTIONS_COLL = module.state.executions_collection

    KNOWLEDGE_INDEX_ENDPOINT  = module.knowledge.index_endpoint_id
    KNOWLEDGE_DEPLOYED_INDEX  = module.knowledge.deployed_index_id
    KNOWLEDGE_ENDPOINT_DOMAIN = module.knowledge.public_endpoint_domain

    # The other half of the `dimensions = 768` decision above.
    EMBEDDING_MODEL = "text-embedding-004"

    VERTEX_LOCATION = module.model_integration.vertex_location
    MODEL_ID        = module.model_integration.model_id
  }

  labels = local.labels
  # Available for a deployment that already runs a VPC; null here, which is what keeps this
  # tree free of the VPC peering the Vertex endpoint would otherwise need.
  vpc_connector = var.vpc_connector

}

module "approval" {
  source = "../../modules/approval"

  project_id         = var.project_id
  name_prefix        = local.name_prefix
  location           = var.region
  firestore_location = var.firestore_location
  kms_key_id         = module.security.kms_key_id

  validator_service_account_email = local.validator_email
  executor_service_account_email  = local.executor_email
  validator_member                = local.validator_member
  executor_member                 = local.executor_member

  orchestrator_member = local.orchestrator_member

  approver_members = var.approver_members

  validator_package_path = var.approval_validator.package_path
  validator_entry_point  = var.approval_validator.entry_point
  executor_package_path  = var.approval_executor.package_path
  executor_entry_point   = var.approval_executor.entry_point
  runtime                = var.approval_validator.runtime

  validator_environment = var.approval_validator.environment

  # Write tool URLs are supplied to the executor and to nothing else.
  executor_environment = merge(var.approval_executor.environment, {
    WRITE_TOOL_URLS = jsonencode(module.tools.write_tool_urls)
  })

  # Must exceed the slowest write tool, or the write completes and the executor is killed
  # before it records the outcome.
  executor_timeout_seconds = 120

  # Every instance is a thing that can move money. A redelivered notification storm should
  # queue rather than fan out.
  executor_max_instances = 3

  common_environment = {
    GCP_PROJECT = var.project_id
  }

  trace_log_name = module.observability.trace_log_name

  # PITR on, as in prod: it changes billing and backup behaviour, so prod should not be the
  # first place it runs. Delete protection off, for the same reason as the execution state
  # database above — this environment gets destroyed on purpose.
  enable_point_in_time_recovery = true
  enable_delete_protection      = false

  # Matches the approval window below. A request that outlives its own window is noise
  # sitting in a queue looking actionable.
  message_retention_duration = "86400s"

  labels = local.labels
  # Available for a deployment that already runs a VPC; null here, which is what keeps this
  # tree free of the VPC peering the Vertex endpoint would otherwise need.
  vpc_connector = var.vpc_connector

}

module "orchestration" {
  source = "../../modules/orchestration"

  project_id  = var.project_id
  name_prefix = local.name_prefix
  location    = var.region

  orchestrator_service_account_email = local.orchestrator_email
  orchestrator_member                = local.orchestrator_member
  caller_members                     = var.caller_members

  # Read tools only. `tool_urls_by_name` would compile and would hand the workflow the
  # address of every write tool.
  read_tool_urls    = module.tools.read_tool_urls
  validator_url     = module.approval.validator_url
  trace_emitter_url = module.observability.trace_emitter_url

  # Prod's budgets, deliberately not relaxed. Loosening them would let staging pass runs
  # prod would cut off at the loop bound, which is the class of failure a release rehearsal
  # most needs to reproduce.
  max_steps                = 10
  approval_timeout_seconds = 86400

  # LOG_ERRORS_ONLY, as in prod, rather than dev's LOG_ALL_CALLS. Call arguments are the
  # payload, and staging is where a production-shaped payload first appears — the same
  # reasoning that sets `log_execution_data = false` in the AWS tree.
  #
  # The cost is the same one prod pays: a stuck execution has to be reconstructed from the
  # trace log rather than read off the step history. Rehearsing that reconstruction is
  # itself worth something.
  call_log_level = "LOG_ERRORS_ONLY"

  # LOCK 2. modules/tools already refuses the orchestrator invoke on these services by
  # granting run.invoker only to the executor; this denies it independently, so a later
  # project-level run.invoker grant cannot quietly reopen the path.
  write_tool_service_names = module.tools.write_tool_service_names

  labels = local.labels
}
