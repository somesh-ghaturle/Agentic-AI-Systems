# Dev environment
#
# The cheapest thing that is still architecturally the same shape as prod. What differs is
# retention, warehouse size and blast radius — never the write boundary, which is identical
# in all three environments because an environment that draws it differently is not a
# rehearsal for anything.

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
  name_prefix = "AGENTIC_DEV"
}

module "state" {
  source = "../../modules/state"

  name_prefix   = local.name_prefix
  database_name = "${local.name_prefix}_DB"

  # Standard edition caps Time Travel at 1 day. Dev has nothing worth recovering.
  data_retention_time_in_days = 1

  warehouse_size       = "XSMALL"
  auto_suspend_seconds = 60
  max_cluster_count    = 1

  # A runaway-loop guard, not a budget — the same posture AWS/Azure/GCP dev takes with
  # daily_cost_threshold_usd = 25. Suspension is on: dev can tolerate a paused warehouse far
  # more easily than it can tolerate an unbounded loop running up credits unnoticed.
  cost_monitor_credit_quota              = 10
  cost_monitor_suspend_trigger           = 100
  cost_monitor_suspend_immediate_trigger = 110
}

module "security" {
  source = "../../modules/security"

  name_prefix    = local.name_prefix
  database_name  = module.state.database_name
  audit_schema   = module.state.audit_schema
  warehouse_name = module.state.warehouse_name

  # No allow-list in dev. An empty list creates no policy — see the variable's own note on
  # why an empty allow-list is not the same as a permissive one.
  allowed_ip_list = []

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

  # Hours, not minutes. The search service resumes a warehouse on every refresh, and in
  # dev nothing is querying it between refreshes.
  target_lag = "24 hours"

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

  archive_retention_days = 1

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

  # Slow in dev. Every sweep resumes a warehouse, and nobody is waiting on an approval here.
  sweep_interval_minutes = 60

  # Off until someone starts it deliberately. See the variable's note.
  task_started = false

  depends_on = [module.approval]
}
