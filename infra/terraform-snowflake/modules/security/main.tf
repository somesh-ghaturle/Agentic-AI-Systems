# Security — the role skeleton, and the two grants that are never made
#
# On AWS the write boundary is a Lambda resource policy; on GCP it is an IAM Deny policy;
# on Azure it is `app_role_assignment_required`. On Snowflake it is the role graph, and
# that makes this module the one that matters most in this tree.
#
# The graph is deliberately a forest, not a tree:
#
#     TOOL_OWNER        owns the write procedures, holds the table privileges.
#                       No user is ever granted this role. Nothing logs in as it.
#
#     EXECUTOR          holds USAGE on write procedures. Nothing else.
#     ORCHESTRATOR      holds USAGE on read procedures. Nothing else.
#     VALIDATOR         writes approval records. No tool privileges at all.
#
# ORCHESTRATOR and EXECUTOR share no ancestor. That is the whole boundary, and it is one
# `snowflake_grant_account_role` away from being nothing — see the note on inheritance
# below, and tests/test_write_boundary.py, which exists to catch exactly that edge.
#
# Snowflake's own SYSADMIN convention is deliberately not followed here. The convention is
# to grant every custom role up to SYSADMIN so that one role can manage everything, which
# is convenient and would hand SYSADMIN the union of ORCHESTRATOR and EXECUTOR — that is,
# a role that can both propose a write and execute it. The convenience is real; it is also
# precisely the thing this architecture exists to prevent, so this tree pays the cost of
# not having it.

terraform {
  required_version = ">= 1.6"
  required_providers {
    snowflake = {
      source  = "snowflakedb/snowflake"
      version = "~> 2.20"
    }
  }
}

# ---------------------------------------------------------------------------
# The four roles
# ---------------------------------------------------------------------------

resource "snowflake_account_role" "tool_owner" {
  name    = "${var.name_prefix}_TOOL_OWNER"
  comment = "Owns write procedures and holds the underlying table privileges. Granted to no user, ever."
}

resource "snowflake_account_role" "orchestrator" {
  name    = "${var.name_prefix}_ORCHESTRATOR"
  comment = "The agent loop. Read tools only. Never reaches a write procedure."
}

resource "snowflake_account_role" "validator" {
  name    = "${var.name_prefix}_VALIDATOR"
  comment = "Validates proposals and writes approval records. Holds no tool privileges."
}

resource "snowflake_account_role" "executor" {
  name    = "${var.name_prefix}_EXECUTOR"
  comment = "The only role holding USAGE on write procedures. Acts only on an approved claim."
}

# The scheduler's role. It is granted EXECUTOR (see modules/orchestration), which makes it
# the one role in this tree that sits *above* a boundary role in the graph. That is safe
# only while nothing grants TASK_OWNER onward to the orchestrator — an edge that would
# hand the orchestrator the executor's grants by inheritance, two hops away and invisible
# in any single file. tests/test_write_boundary.py walks the graph transitively for
# exactly this reason.
resource "snowflake_account_role" "task_owner" {
  name    = "${var.name_prefix}_TASK_OWNER"
  comment = "Owns the approval sweeper task. Inherits EXECUTOR. Granted to no user and to no other role."
}

resource "snowflake_account_role" "auditor" {
  name    = "${var.name_prefix}_AUDITOR"
  comment = "Read-only on the AUDIT schema. For humans reconstructing an incident."
}

# ---------------------------------------------------------------------------
# Warehouse and database usage
#
# USAGE on a warehouse is not a privilege on data — without it, a role holding every table
# grant in the account still cannot run a query, because it has nothing to run it on.
# Granting it to all five roles is correct and is not a weakening of anything.
# ---------------------------------------------------------------------------

locals {
  all_roles = {
    tool_owner   = snowflake_account_role.tool_owner.name
    orchestrator = snowflake_account_role.orchestrator.name
    validator    = snowflake_account_role.validator.name
    executor     = snowflake_account_role.executor.name
    auditor      = snowflake_account_role.auditor.name
    task_owner   = snowflake_account_role.task_owner.name
  }
}

resource "snowflake_grant_privileges_to_account_role" "warehouse_usage" {
  for_each = local.all_roles

  account_role_name = each.value
  privileges        = ["USAGE"]

  on_account_object {
    object_type = "WAREHOUSE"
    object_name = var.warehouse_name
  }
}

resource "snowflake_grant_privileges_to_account_role" "database_usage" {
  for_each = local.all_roles

  account_role_name = each.value
  privileges        = ["USAGE"]

  on_account_object {
    object_type = "DATABASE"
    object_name = var.database_name
  }
}

# ---------------------------------------------------------------------------
# Network policy
#
# Snowflake is a public endpoint. Unlike the other three trees, there is no VPC to put
# this inside — a private-link path exists but is an account-level purchase and a
# different conversation. What is available at no cost is an allow-list, and applying it
# to the service users rather than the account is deliberate: an account-level policy that
# locks out a human admin during an incident is a policy someone disables permanently.
# ---------------------------------------------------------------------------

resource "snowflake_network_policy" "main" {
  count = length(var.allowed_ip_list) > 0 ? 1 : 0

  name            = "${var.name_prefix}_NETWORK_POLICY"
  allowed_ip_list = var.allowed_ip_list
  blocked_ip_list = var.blocked_ip_list
  comment         = "Ingress allow-list for the agentic service users."
}

# ---------------------------------------------------------------------------
# Masking
#
# The counterpart to the Bedrock guardrail's PII config on AWS and Model Armor on GCP,
# and it works at the opposite end. Those filter what reaches or leaves the model; this
# filters what leaves the *table* — so a retrieved document carrying an email address is
# masked before the orchestrator ever assembles it into a prompt.
#
# That ordering matters and is the reason this exists in addition to the model-layer
# filter. PRODUCTION-PRINCIPLES.md is explicit that masking happens before data reaches
# the model; a model-boundary filter is a backstop for what upstream masking missed. This
# is the upstream masking.
#
# EXEMPT_OTHER_POLICIES is left off. It exists so a masking policy can be applied to a
# column already protected by another policy, and turning it on is how a column ends up
# with two policies that disagree.
# ---------------------------------------------------------------------------

resource "snowflake_masking_policy" "email" {
  count = var.create_masking_policies ? 1 : 0

  database         = var.database_name
  schema           = var.audit_schema
  name             = "${var.name_prefix}_MASK_EMAIL"
  return_data_type = "VARCHAR"
  comment          = "Masks email addresses for every role except the auditor."

  argument {
    name = "VAL"
    type = "VARCHAR"
  }

  # CURRENT_ROLE() rather than IS_ROLE_IN_SESSION(): the latter is true for any role
  # *inherited* by the session, so a role granted the auditor role anywhere in its
  # ancestry would see unmasked values. CURRENT_ROLE() is the active role and nothing
  # else, which is the check this policy means.
  body = <<-SQL
    CASE
      WHEN CURRENT_ROLE() = '${snowflake_account_role.auditor.name}' THEN VAL
      ELSE REGEXP_REPLACE(VAL, '^[^@]+', '****')
    END
  SQL
}
