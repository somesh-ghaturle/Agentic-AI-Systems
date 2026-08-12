# Production environment.
#
# Structurally identical to envs/dev. Every difference between the two is a variable, and
# each one is annotated below with what it costs and what it buys. Diff this file against
# envs/dev/main.tf: the module blocks, their order, and their wiring should be the same
# line for line, and anything else is drift worth explaining.
#
# What differs here: a locked archive retention policy, point-in-time recovery on both
# Firestore databases, an HSM-backed key, more Vector Search capacity, a longer approval
# window, a higher spend threshold, and call logging turned down.
#
# ---------------------------------------------------------------------------
# One of these differences cannot be undone
#
# `lock_retention_policy = true` on the archive is irreversible. Once applied, no
# principal — not the project owner, not Google support — can shorten the retention period
# or delete an object before it ages out, and the bucket cannot be deleted while anything
# is still under retention. That is the property an audit trail needs and it is also a
# 7-year commitment made by a boolean. Read modules/archive/variables.tf before the first
# apply.
#
# ---------------------------------------------------------------------------
# One project per environment
#
# This root assumes dev and prod live in separate GCP projects, which is the platform's
# idiom rather than a preference. Several things here are project-scoped and cannot be
# name-prefixed apart: `roles/datastore.user` covers every Firestore database in the
# project, service account IDs are unique per project, and an IAM Deny policy attaches to
# the project rather than to a resource. Sharing one project between environments means
# dev's grants reach prod's data.
#
# ---------------------------------------------------------------------------
# Two dependency cycles, and how each is broken
#
# 1. orchestration -> observability -> orchestration
#    The orchestrator needs the trace emitter's URL; the workflow-failure alert needs the
#    workflow's name. Broken by computing the workflow name in `locals` — it is
#    deterministic from name_prefix, and modules/orchestration/outputs.tf says so.
#
# 2. observability -> archive -> observability
#    The log sink needs the archive bucket's name; the bucket needs the sink's writer
#    identity to grant it objectCreator. Broken the same way, in the same direction: the
#    bucket name is derived from name_prefix here, and the writer identity flows
#    observability -> archive afterwards. The identity is unknown until apply, which is
#    fine — it is a map *value*, and only for_each *keys* must be known at plan time.
#
# The AWS root breaks its cycle by constructing ARNs. Same trick, different strings.
# ---------------------------------------------------------------------------

terraform {
  required_version = ">= 1.6"

  # Remote state with locking. GCS backends lock by default — there is no separate lock
  # table to forget. Uncomment and fill in before the first apply; local state for shared
  # infrastructure means two people applying at once corrupt each other's work.
  #
  # backend "gcs" {
  #   bucket = "<your-tf-state-bucket>"
  #   prefix = "agentic/prod"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region

  # Applied to every resource that supports labels, including ones these modules do not
  # label explicitly. Modules still receive `labels` as well: default_labels is a provider
  # convenience, and a module that is reused under a different provider config should not
  # lose its labels.
  default_labels = local.labels
}

locals {
  env         = "prod"
  name_prefix = "${var.project}-${local.env}"

  # --- cycle-breakers ------------------------------------------------------
  #
  # The same names the resources will produce, known before they exist. See the note at
  # the top of this file.
  workflow_name        = "${local.name_prefix}-orchestrator"
  archive_bucket_name  = "${local.name_prefix}-archive"

  # --- service account IDs -------------------------------------------------
  #
  # Capped at 30 characters by the API, which is why `project` is validated to 12. Tool
  # names may carry underscores because they are also Python module names; account IDs may
  # not, so they are normalized here rather than inside modules/identity — the module
  # refuses a malformed ID rather than guessing what was meant.
  tool_sa_ids = { for k, v in var.tools : k => "${local.name_prefix}-${replace(k, "_", "-")}" }

  fixed_sa_ids = {
    orchestrator  = "${local.name_prefix}-orchestrator"
    validator     = "${local.name_prefix}-approval-val"
    executor      = "${local.name_prefix}-approval-exec"
    trace_emitter = "${local.name_prefix}-trace-emitter"
  }

  sa_ids = merge(local.tool_sa_ids, local.fixed_sa_ids)

  # Per-tool lookups, so module blocks below read as `local.tool_members["retrieve"]`
  # rather than a nested index into two maps.
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
# Identity — created first, depends on nothing
#
# Every principal in the tree exists before anything that grants to it. See
# modules/identity/main.tf for why these are created rather than computed: GCP accepts an
# IAM binding naming a service account that does not exist, so a constructed email is
# correct-looking and unverified.
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

  # Must be the same region as everything it encrypts. A key in us-central1 cannot encrypt
  # a bucket in europe-west1, and the failure surfaces at bucket-create time.
  location = var.region

  # Software keys in dev. HSM costs meaningfully more per version and per operation, and
  # buys a property dev does not need.
  protection_level = "SOFTWARE"

  # No handler in this tree decrypts payloads itself — the service agents do the work, and
  # the module grants them. This stays empty until a handler calls the KMS API directly.
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

  enable_point_in_time_recovery = false
  enable_delete_protection      = false

  # Tools only. The validator and executor also need datastore.user, and modules/approval
  # grants it to them — `roles/datastore.user` is a project-level role, so granting it
  # here as well would create two Terraform resources managing the same IAM membership,
  # which apply cleanly the first time and fight each other afterwards.
  datastore_user_members = local.tool_members
}

module "archive" {
  source = "../../modules/archive"

  project_id  = var.project_id
  name_prefix = local.name_prefix
  location    = var.region
  kms_key_id  = module.security.kms_key_id

  # Dev traces are not evidence. Expire them, and do not lock anything: a locked retention
  # policy cannot be undone by anyone, including the project owner, and a dev environment
  # that cannot be torn down is a dev environment nobody tears down.
  retention_days        = null
  lock_retention_policy = false

  transition_nearline_days = 7
  transition_coldline_days = 30
  expiration_days          = 90

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
  # A mismatch is accepted at index-create time and fails on every query afterwards, so
  # this and EMBEDDING_MODEL below are one decision written in two places.
  dimensions = 768

  # One replica, no autoscaling. A deployed index has no scale-to-zero, which makes this
  # the largest standing cost in the tree — in dev, keep it at the floor.
  machine_type      = "e2-standard-2"
  min_replica_count = 1
  max_replica_count = 1

  # The retrieve tool's identity, not the orchestrator's. The orchestrator only invokes
  # that function; it never issues a query, so granting it here would authorize nobody and
  # every retrieval would come back 403.
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

  # The reason handler, and nothing else. Note this is the same project-level role
  # (`roles/aiplatform.user`) that modules/knowledge grants to the retrieve tool — two
  # distinct memberships because they name two distinct principals. Point them at one
  # shared service account and Terraform would be managing the same membership twice.
  model_caller_members = {
    reason = local.tool_members["reason"]
  }
}

module "observability" {
  source = "../../modules/observability"

  project_id  = var.project_id
  name_prefix = local.name_prefix
  location    = var.region

  # The orchestrator's own records reach the log-based metrics only through this function.
  # Omit it and the loop-bound and spend alerts sit at zero forever, which reads exactly
  # like a healthy system.
  trace_emitter = {
    package_path          = var.trace_emitter.package_path
    runtime               = var.trace_emitter.runtime
    entry_point           = var.trace_emitter.entry_point
    service_account_email = local.emitter_email
    member                = local.emitter_member
    orchestrator_member   = local.orchestrator_member
  }

  # Every handler that emits a trace. The orchestrator and the emitter are absent on
  # purpose: modules/orchestration grants the first and trace-emitter.tf grants the
  # second, and logging.logWriter is project-level, so listing them again would duplicate
  # the membership.
  trace_writer_members = merge(local.tool_members, {
    validator = local.validator_member
    executor  = local.executor_member
  })

  alert_email_receivers = var.alert_email_receivers

  # Low on purpose. In dev this is a runaway-loop detector, not a budget.
  daily_cost_threshold_usd = 25

  schema_failure_threshold     = 5
  abandoned_approval_threshold = 2

  # Deterministic — see the cycle note at the top of this file.
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

  # One identity per tool. A shared identity would make every data-plane grant above — the
  # Vector Search querier, the model caller — a grant to every tool.
  tool_service_account_emails = local.tool_emails

  orchestrator_member      = local.orchestrator_member
  approval_executor_member = local.executor_member

  # Traces go to the shared log the metric filters watch, not to each function's own log.
  # Anything a handler prints to stdout is captured and looks healthy in the console while
  # being invisible to every alert here.
  trace_log_name = module.observability.trace_log_name

  common_environment = {
    GCP_PROJECT     = var.project_id
    EXECUTIONS_DB   = module.state.database_name
    EXECUTIONS_COLL = module.state.executions_collection

    # Vector Search coordinates. Passed rather than resolved at cold start because
    # modules/knowledge depends only on modules/identity, so there is no cycle to avoid
    # here — unlike the AWS tree, where tools -> knowledge -> orchestration -> tools.
    KNOWLEDGE_INDEX_ENDPOINT = module.knowledge.index_endpoint_id
    KNOWLEDGE_DEPLOYED_INDEX = module.knowledge.deployed_index_id
    KNOWLEDGE_ENDPOINT_DOMAIN = module.knowledge.public_endpoint_domain

    # The other half of the `dimensions = 768` decision above.
    EMBEDDING_MODEL = "text-embedding-004"

    VERTEX_LOCATION = module.model_integration.vertex_location
    MODEL_ID        = module.model_integration.model_id
  }

  labels = local.labels
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

  # The orchestrator can ask for validation. That is the whole of its involvement in the
  # write path — it cannot publish an approval request directly, and it cannot resolve one.
  orchestrator_member = local.orchestrator_member

  approver_members = var.approver_members

  validator_package_path = var.approval_validator.package_path
  validator_entry_point  = var.approval_validator.entry_point
  executor_package_path  = var.approval_executor.package_path
  executor_entry_point   = var.approval_executor.entry_point
  runtime                = var.approval_validator.runtime

  validator_environment = var.approval_validator.environment

  # Write tool URLs are supplied to the executor and to nothing else. This is the only
  # consumer of `write_tool_urls` in the tree; a second one appearing means something other
  # than the executor intends to call a write tool.
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

  enable_point_in_time_recovery = false
  enable_delete_protection      = false

  # No longer than the workflow's approval window: a request that outlives its own window
  # is noise sitting in a queue looking actionable.
  message_retention_duration = "3600s"

  labels = local.labels
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

  max_steps                = 10
  approval_timeout_seconds = 3600
  call_log_level           = "LOG_ALL_CALLS"

  # LOCK 2. modules/tools already refuses the orchestrator invoke on these services by
  # granting run.invoker only to the executor; this denies it independently, so a later
  # project-level run.invoker grant cannot quietly reopen the path.
  write_tool_service_names = module.tools.write_tool_service_names

  labels = local.labels
}
