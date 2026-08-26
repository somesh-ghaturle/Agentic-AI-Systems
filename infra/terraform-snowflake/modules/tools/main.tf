# Tools — the read/write split, expressed as procedure grants
#
# The architecture's rule is that read tools are ungated and write tools are reachable
# only through the approval executor. Each cloud spells that differently. Here it is:
#
#   1. Every tool is a stored procedure with EXECUTE AS OWNER, owned by TOOL_OWNER.
#   2. TOOL_OWNER holds the table privileges. No caller role holds them directly.
#   3. USAGE on a read procedure goes to ORCHESTRATOR.
#   4. USAGE on a write procedure goes to EXECUTOR, and to nothing else.
#
# Point 2 is what makes point 4 worth having. With EXECUTE AS OWNER the caller needs only
# USAGE on the procedure — the procedure body runs with TOOL_OWNER's privileges. So a
# compromised EXECUTOR holds exactly the procedures it was granted and cannot reach the
# tables underneath to write to them directly. A compromised ORCHESTRATOR holds the read
# procedures and nothing else.
#
# EXECUTE AS CALLER would invert this: the body would run with the caller's privileges,
# so the boundary would only hold as long as no caller was ever granted a table privilege
# — a much weaker claim, and one that decays every time someone adds a grant elsewhere.
# It fails closed rather than open (the write errors instead of succeeding), which is why
# it is a correctness bug rather than a breach, but the test suite still asserts against
# it because a fail-closed write boundary is an outage nobody can diagnose.
#
# What this module cannot defend against on its own is a FUTURE GRANT. `GRANT USAGE ON
# FUTURE PROCEDURES IN SCHEMA TOOLS TO ROLE ORCHESTRATOR` is one statement, is a perfectly
# valid grant, is invisible in a diff of this file, and silently covers every write
# procedure added afterwards. Two things stand against it: `with_managed_access` on the
# TOOLS schema (modules/state), which stops procedure owners delegating, and the policy in
# infra/policies/guardrail_wiring.rego, which fails the build if such a grant appears.

terraform {
  required_version = ">= 1.6"
  required_providers {
    snowflake = {
      source  = "snowflakedb/snowflake"
      version = "~> 2.20"
    }
  }
}

locals {
  # A Snowflake procedure is identified by name *and* argument types — `RETRIEVE(VARCHAR)`
  # and `RETRIEVE(VARCHAR, NUMBER)` are two different objects. Grants must name the full
  # signature, so it is built once here rather than at each use site.
  read_signatures = {
    for k, v in var.read_tools :
    k => "${var.database_name}.${var.schema_name}.${upper(k)}(${join(", ", [for a in v.arguments : a.type])})"
  }

  write_signatures = {
    for k, v in var.write_tools :
    k => "${var.database_name}.${var.schema_name}.${upper(k)}(${join(", ", [for a in v.arguments : a.type])})"
  }
}

# ---------------------------------------------------------------------------
# Read tools — ungated
#
# Ungated is a deliberate decision, not an oversight, and THREAT-MODEL.md names it as the
# largest genuine gap in the architecture: a prompt-injected model reads anything the read
# tools reach. The answer is to scope what the read tools return, not to gate them.
# ---------------------------------------------------------------------------

resource "snowflake_procedure_sql" "read" {
  for_each = var.read_tools

  database = var.database_name
  schema   = var.schema_name
  name     = upper(each.key)

  return_type          = each.value.return_type
  procedure_definition = each.value.definition
  comment              = "Read tool. Ungated: callable by the orchestrator."

  # See the module header. OWNER is what keeps table privileges off the caller.
  execute_as = "OWNER"

  dynamic "arguments" {
    for_each = each.value.arguments
    content {
      arg_name      = arguments.value.name
      arg_data_type = arguments.value.type
    }
  }
}

# ---------------------------------------------------------------------------
# Write tools — the gated side
# ---------------------------------------------------------------------------

resource "snowflake_procedure_sql" "write" {
  for_each = var.write_tools

  database = var.database_name
  schema   = var.schema_name
  name     = upper(each.key)

  return_type          = each.value.return_type
  procedure_definition = each.value.definition
  comment              = "WRITE TOOL. Callable only by the approval executor, and only on an approved claim."

  execute_as = "OWNER"

  dynamic "arguments" {
    for_each = each.value.arguments
    content {
      arg_name      = arguments.value.name
      arg_data_type = arguments.value.type
    }
  }
}

# ---------------------------------------------------------------------------
# Ownership
#
# Terraform creates these procedures as whatever role the provider is running under. Left
# alone, that role owns them — and an object's owner can always execute it, which would
# put a second principal inside the write boundary without anyone writing a grant.
# Transferring ownership to TOOL_OWNER is what closes that.
#
# OUTBOUND_PRIVILEGES = "COPY" preserves grants already made on the object through the
# transfer. The alternative, REVOKE, drops them, which would silently un-wire the
# executor's USAGE on the next apply that touched ownership.
# ---------------------------------------------------------------------------

resource "snowflake_grant_ownership" "read" {
  for_each = var.read_tools

  account_role_name   = var.tool_owner_role
  outbound_privileges = "COPY"

  on {
    object_type = "PROCEDURE"
    object_name = local.read_signatures[each.key]
  }

  depends_on = [snowflake_procedure_sql.read]
}

resource "snowflake_grant_ownership" "write" {
  for_each = var.write_tools

  account_role_name   = var.tool_owner_role
  outbound_privileges = "COPY"

  on {
    object_type = "PROCEDURE"
    object_name = local.write_signatures[each.key]
  }

  depends_on = [snowflake_procedure_sql.write]
}

# ---------------------------------------------------------------------------
# The grants that draw the line
#
# These two resources are the write boundary. Everything above is arrangement.
# ---------------------------------------------------------------------------

resource "snowflake_grant_privileges_to_account_role" "read_to_orchestrator" {
  for_each = var.read_tools

  account_role_name = var.orchestrator_role
  privileges        = ["USAGE"]

  on_schema_object {
    object_type = "PROCEDURE"
    object_name = local.read_signatures[each.key]
  }

  depends_on = [snowflake_grant_ownership.read]
}

# The executor, and nothing else. There is deliberately no companion resource granting
# these to the orchestrator, and adding one is the change tests/test_write_boundary.py
# exists to fail on.
resource "snowflake_grant_privileges_to_account_role" "write_to_executor" {
  for_each = var.write_tools

  account_role_name = var.executor_role
  privileges        = ["USAGE"]

  on_schema_object {
    object_type = "PROCEDURE"
    object_name = local.write_signatures[each.key]
  }

  depends_on = [snowflake_grant_ownership.write]
}

# ---------------------------------------------------------------------------
# Table privileges — held by TOOL_OWNER alone
#
# This is point 2 from the header, and it is what makes the USAGE grants above mean
# something. If a caller role also held INSERT on the underlying table, the procedure
# boundary would be decoration: the caller could skip the procedure and write directly.
# ---------------------------------------------------------------------------

resource "snowflake_grant_privileges_to_account_role" "tool_owner_tables" {
  for_each = var.write_table_names

  account_role_name = var.tool_owner_role
  privileges        = ["SELECT", "INSERT", "UPDATE"]

  on_schema_object {
    object_type = "TABLE"
    object_name = each.value
  }
}
