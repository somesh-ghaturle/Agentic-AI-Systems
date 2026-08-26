# Staging environment
#
# The environment that exists to make prod boring. It carries prod's guardrails — the
# network allow-list, masking, a running sweeper — at dev's scale, so that a change which
# is going to fail on a policy fails here first rather than at 3am.
#
# Two things are deliberately prod-like and cost money to keep that way: the sweeper runs
# on prod's cadence, and the network policy is enforced. Relaxing either would make
# staging cheaper and would remove the only reason to have it.

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
  name_prefix = "AGENTIC_STAGING"
}

module "state" {
  source = "../../modules/state"

  name_prefix   = local.name_prefix
  database_name = "${local.name_prefix}_DB"

  # Longer than dev, shorter than prod. Enough to recover from a bad migration rehearsed
  # here, not enough to pretend this is a system of record.
  data_retention_time_in_days = 7

  warehouse_size       = "XSMALL"
  auto_suspend_seconds = 60
  max_cluster_count    = 1
}

module "security" {
  source = "../../modules/security"

  name_prefix    = local.name_prefix
  database_name  = module.state.database_name
  audit_schema   = module.state.audit_schema
  warehouse_name = module.state.warehouse_name

  # Enforced here, unlike dev. Staging is where a CIDR someone forgot to add fails
  # visibly, which is the entire point of having the environment.
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

  # Closer to prod's freshness so index-refresh cost is observed here rather than
  # discovered on the prod bill.
  target_lag = "4 hours"

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

  archive_retention_days = 7

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

  # Prod's cadence. An approval path that is only ever exercised at hourly resolution is
  # an approval path nobody has actually tested.
  sweep_interval_minutes = 5

  task_started = var.task_started

  depends_on = [module.approval]
}
