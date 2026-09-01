# Production environment
#
# Everything the other two roots relax, this one does not. The differences from dev are
# retention, scale and enforcement — the write boundary is byte-for-byte the same set of
# grants, because a boundary that differs by environment has not been tested by any
# environment.
#
# The expensive choices here are deliberate and each buys something specific:
#
#   data_retention 30d   Time Travel over the approvals table. This is the audit trail;
#                        30 is the Enterprise maximum and the reason to be on Enterprise.
#   multi-cluster 3      Approval sweeps and agent queries stop queueing behind each other.
#   allow-list enforced  The service users authenticate from known networks only.
#   sweeper started      Approvals are noticed without a human starting a task first.

terraform {
  required_version = ">= 1.6"
  required_providers {
    snowflake = {
      source  = "snowflakedb/snowflake"
      version = "~> 2.20"
    }
  }
}

provider "snowflake" {
  organization_name = var.organization_name
  account_name      = var.account_name

  # Workload identity federation. No key, no password, no token in this configuration or
  # in the state file it produces — see modules/identity for why that was chosen over
  # key-pair auth, and docs/SECRETS-ROTATION.md for what it means for the repository as a
  # whole.
  #
  # `user` is deliberately absent: under WORKLOAD_IDENTITY the user is resolved from the
  # federated identity presented, and naming one here is how you get a confusing 390144
  # when the two disagree.
  authenticator              = "WORKLOAD_IDENTITY"
  workload_identity_provider = var.workload_identity_provider
  role                       = var.terraform_role

  # Several resources this tree depends on are still preview in the provider. They are
  # listed rather than suppressed wholesale so that a future provider release promoting
  # one produces a visible diff here instead of silently changing behaviour.
  preview_features_enabled = [
    "snowflake_table_resource",
    "snowflake_hybrid_table_resource",
    "snowflake_procedure_sql_resource",
    "snowflake_cortex_search_service_resource",
    "snowflake_network_policy_attachment_resource",
  ]
}

locals {
  name_prefix = "AGENTIC_PROD"
}

module "state" {
  source = "../../modules/state"

  name_prefix   = local.name_prefix
  database_name = "${local.name_prefix}_DB"

  # The Enterprise maximum. The approvals table lives in this database and it is the
  # record of who authorized what — a mistaken UPDATE against it is exactly the case Time
  # Travel exists for, and 30 days is the widest window Snowflake will sell.
  data_retention_time_in_days = 30

  warehouse_size       = var.warehouse_size
  auto_suspend_seconds = 60

  # Multi-cluster, so an approval sweep does not queue behind a long retrieval. This
  # scales concurrency, not speed: it does not make any single query faster.
  max_cluster_count = 3

  # Notify-only by default: no suspend_trigger is set here, so a real traffic spike cannot
  # auto-suspend production the way it deliberately can in dev and staging. See
  # cost_monitor_credit_quota's own description for why null is the default rather than a
  # guessed number.
  cost_monitor_credit_quota = var.cost_monitor_credit_quota
}

module "security" {
  source = "../../modules/security"

  name_prefix    = local.name_prefix
  database_name  = module.state.database_name
  audit_schema   = module.state.audit_schema
  warehouse_name = module.state.warehouse_name

  # Required in prod. The variable has no default here for that reason — an accidentally
  # empty allow-list in prod would create no policy at all, which fails open.
  allowed_ip_list = var.allowed_ip_list

  create_masking_policies = true
}

module "identity" {
  source = "../../modules/identity"

  name_prefix    = local.name_prefix
  database_name  = module.state.database_name
  warehouse_name = module.state.warehouse_name

  service_users = {
    orchestrator = {
      role              = module.security.orchestrator_role
      comment           = "The agent loop. Read tools and the guarded model entry point."
      default_schema    = module.state.app_schema
      workload_identity = { aws_role_arn = var.orchestrator_workload_arn }
    }
    executor = {
      role              = module.security.executor_role
      comment           = "The approval executor. The only identity that reaches a write tool."
      default_schema    = module.state.app_schema
      workload_identity = { aws_role_arn = var.executor_workload_arn }
    }
  }

  network_policy_name = module.security.network_policy_name
}

module "model" {
  source = "../../modules/model"

  database_name = module.state.database_name
  schema_name   = module.state.tools_schema

  tool_owner_role   = module.security.tool_owner_role
  orchestrator_role = module.security.orchestrator_role

  model_name  = var.model_name
  temperature = 0
  max_tokens  = 4096
}

module "knowledge" {
  source = "../../modules/knowledge"

  name_prefix    = local.name_prefix
  database_name  = module.state.database_name
  schema_name    = module.state.app_schema
  warehouse_name = module.state.warehouse_name

  # The freshness contract users actually feel. Every refresh resumes a warehouse, so this
  # is the largest standing cost in the tree after the sweeper.
  target_lag = "1 hour"

  orchestrator_role = module.security.orchestrator_role

  document_reader_roles = {
    orchestrator = module.security.orchestrator_role
    auditor      = module.security.auditor_role
  }
}

module "tools" {
  source = "../../modules/tools"

  database_name = module.state.database_name
  schema_name   = module.state.tools_schema

  tool_owner_role   = module.security.tool_owner_role
  orchestrator_role = module.security.orchestrator_role
  executor_role     = module.security.executor_role

  read_tools = {
    retrieve = {
      return_type = "VARIANT"
      arguments   = [{ name = "QUERY", type = "VARCHAR" }]
      definition  = <<-SQL
        BEGIN
          RETURN (
            SELECT ARRAY_AGG(OBJECT_CONSTRUCT('doc_id', DOC_ID, 'title', TITLE))
              FROM ${module.state.database_name}.${module.state.app_schema}.DOCUMENTS
             WHERE CONTAINS(LOWER(CONTENT), LOWER(:QUERY))
             LIMIT 10
          );
        END;
      SQL
    }
  }

  write_tools = {
    # Idempotent on APPROVAL_ID, which is not decoration — the approval gate's stale-claim
    # recovery may invoke this twice for one human approval, and the MERGE is what makes
    # the second invocation return the first one's result instead of refunding twice.
    process_refund = {
      return_type = "VARCHAR"
      arguments = [
        { name = "APPROVAL_ID", type = "VARCHAR" },
        { name = "ORDER_ID", type = "VARCHAR" },
        { name = "AMOUNT_CENTS", type = "NUMBER" },
      ]
      definition = <<-SQL
        BEGIN
          MERGE INTO ${module.state.database_name}.${module.state.app_schema}.REFUNDS t
          USING (SELECT :APPROVAL_ID AS APPROVAL_ID) s
             ON t.APPROVAL_ID = s.APPROVAL_ID
          WHEN NOT MATCHED THEN
            INSERT (APPROVAL_ID, ORDER_ID, AMOUNT_CENTS, PROCESSED_AT)
            VALUES (:APPROVAL_ID, :ORDER_ID, :AMOUNT_CENTS, SYSDATE());
          RETURN 'PROCESSED';
        END;
      SQL
    }
  }

  write_table_names = [
    "${module.state.database_name}.${module.state.app_schema}.REFUNDS",
  ]
}

module "approval" {
  source = "../../modules/approval"

  database_name = module.state.database_name
  schema_name   = module.state.app_schema

  tool_owner_role   = module.security.tool_owner_role
  orchestrator_role = module.security.orchestrator_role
  executor_role     = module.security.executor_role
  auditor_role      = module.security.auditor_role

  # Must exceed the write tool's own timeout plus retries. The warehouse statement timeout
  # is 300s, so 900 leaves room for two retries and then some.
  stale_claim_seconds = 900

  approver_roles = var.approver_roles
}

module "observability" {
  source = "../../modules/observability"

  name_prefix   = local.name_prefix
  database_name = module.state.database_name
  schema_name   = module.state.audit_schema

  trace_writer_roles = {
    orchestrator = module.security.orchestrator_role
    executor     = module.security.executor_role
    validator    = module.security.validator_role
  }

  trace_reader_roles = {
    auditor = module.security.auditor_role
  }
}

module "archive" {
  source = "../../modules/archive"

  name_prefix   = local.name_prefix
  database_name = module.state.database_name
  schema_name   = module.state.audit_schema

  archive_retention_days = 30

  reader_roles = {
    auditor = module.security.auditor_role
  }
}

# ---------------------------------------------------------------------------
# The business table the write tool writes to
#
# Deliberately here rather than in a module. Every other object in this tree is
# infrastructure the architecture calls for; this one is the demo's own data, and putting
# it in modules/ would imply that "agentic systems need a refunds table". They do not.
# It is the thing `process_refund` refunds, and it exists so the write boundary has
# something real on the far side of it.
#
# Hybrid, for the same reason the approvals table is: the MERGE in `process_refund` relies
# on primary-key enforcement to be idempotent, and a standard table has none.
# ---------------------------------------------------------------------------

resource "snowflake_hybrid_table" "refunds" {
  database = module.state.database_name
  schema   = module.state.app_schema
  name     = "REFUNDS"
  comment  = "Demo business table. What process_refund writes to."

  column {
    name     = "APPROVAL_ID"
    type     = "VARCHAR(64)"
    not_null = true
  }
  column {
    name     = "ORDER_ID"
    type     = "VARCHAR(64)"
    not_null = true
  }
  column {
    name     = "AMOUNT_CENTS"
    type     = "NUMBER(12,0)"
    not_null = true
  }
  column {
    name     = "PROCESSED_AT"
    type     = "TIMESTAMP_NTZ"
    not_null = true
  }

  primary_key_constraint {
    name    = "PK_REFUNDS"
    columns = ["APPROVAL_ID"]
  }
}

module "orchestration" {
  source = "../../modules/orchestration"

  name_prefix    = local.name_prefix
  database_name  = module.state.database_name
  schema_name    = module.state.app_schema
  warehouse_name = module.state.warehouse_name

  task_owner_role = module.security.task_owner_role
  executor_role   = module.security.executor_role

  # Five minutes is the approval latency a human waiting on a refund actually experiences.
  sweep_interval_minutes = 5

  # Running. Prod is the one environment where an unstarted sweeper is an outage rather
  # than a default.
  task_started = true

  depends_on = [module.approval]
}
