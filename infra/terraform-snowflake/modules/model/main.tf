# Model integration — Cortex, and the guardrail that only works if nothing can go round it
#
# Claude runs on Cortex here, which puts this tree with AWS and GCP rather than with Azure.
# See docs/DECISION-LOGS/0002-azure-openai-vs-claude.md for why Azure diverges; the short
# version is that the model vendor follows the cloud's first-party offering, and Snowflake's
# is Cortex.
#
# The guardrail on this cloud is CORTEX_GUARD, an option on COMPLETE rather than a separate
# object. That difference is the whole design problem of this module. On AWS a guardrail is
# a resource you attach a version to; on GCP it is a template plus a floor setting that
# makes it account-wide. On Snowflake there is no floor setting — a caller holding the
# CORTEX_USER database role can call SNOWFLAKE.CORTEX.COMPLETE directly, with no guard, and
# nothing anywhere reports it.
#
# So the guard is wired structurally instead:
#
#   1. A wrapper procedure calls COMPLETE with cortex_guard enabled. Always.
#   2. TOOL_OWNER holds SNOWFLAKE.CORTEX_USER. It owns the wrapper, so the wrapper works.
#   3. ORCHESTRATOR holds USAGE on the wrapper and does NOT hold CORTEX_USER.
#
# Step 3 is the wiring. Grant CORTEX_USER to the orchestrator "so it can also summarise
# something" and the guard is bypassable from that moment on, with the wrapper still
# sitting there looking like a control. That is the same failure the other three trees
# name — declared but not wired — and infra/policies/guardrail_wiring.rego fails the build
# on it here exactly as it does for the other three.

terraform {
  required_version = ">= 1.6"
  required_providers {
    snowflake = {
      source  = "snowflakedb/snowflake"
      version = "~> 2.20"
    }
  }
}

# The tool owner may call Cortex directly. It is the role nothing logs in as, and it is
# the owner of the wrapper below — which is what makes EXECUTE AS OWNER work.
resource "snowflake_grant_database_role" "cortex_to_tool_owner" {
  database_role_name = "SNOWFLAKE.CORTEX_USER"
  parent_role_name   = var.tool_owner_role
}

# ---------------------------------------------------------------------------
# The guarded entry point
#
# `cortex_guard` filters the model's *output* — it is Snowflake's safety classifier over
# completions, not an input filter, and it does not defend against prompt injection.
# Nothing on any of the four clouds does. The write boundary is what defends against
# injection; this reduces the odds of the model returning something harmful when it was
# not attacked at all, which is a different and smaller problem worth solving cheaply.
# ---------------------------------------------------------------------------

resource "snowflake_procedure_sql" "complete_guarded" {
  database = var.database_name
  schema   = var.schema_name
  name     = "COMPLETE_GUARDED"

  return_type = "VARCHAR"
  execute_as  = "OWNER"
  comment     = "The only model entry point the orchestrator holds. Always applies cortex_guard."

  arguments {
    arg_name      = "PROMPT"
    arg_data_type = "VARCHAR"
  }

  procedure_definition = <<-SQL
    BEGIN
      RETURN SNOWFLAKE.CORTEX.COMPLETE(
        '${var.model_name}',
        [ { 'role': 'user', 'content': :PROMPT } ],
        { 'guardrails': TRUE, 'temperature': ${var.temperature}, 'max_tokens': ${var.max_tokens} }
      ):choices[0]:messages::VARCHAR;
    END;
  SQL

  depends_on = [snowflake_grant_database_role.cortex_to_tool_owner]
}

resource "snowflake_grant_ownership" "complete_guarded" {
  account_role_name   = var.tool_owner_role
  outbound_privileges = "COPY"

  on {
    object_type = "PROCEDURE"
    object_name = local.complete_signature
  }

  depends_on = [snowflake_procedure_sql.complete_guarded]
}

locals {
  complete_signature = "${var.database_name}.${var.schema_name}.COMPLETE_GUARDED(VARCHAR)"
}

# The orchestrator gets the wrapper and only the wrapper. There is deliberately no
# companion `snowflake_grant_database_role` handing it SNOWFLAKE.CORTEX_USER — adding one
# is what the policy fails on.
resource "snowflake_grant_privileges_to_account_role" "complete_to_orchestrator" {
  account_role_name = var.orchestrator_role
  privileges        = ["USAGE"]

  on_schema_object {
    object_type = "PROCEDURE"
    object_name = local.complete_signature
  }

  depends_on = [snowflake_grant_ownership.complete_guarded]
}
