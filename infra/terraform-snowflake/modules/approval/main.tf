# Approval — the gate
#
# "The model proposes. Application code decides. A human authorizes. The tool executes."
#
# The claim primitive is the part that differs per cloud, and this tree adds a fourth
# spelling to the three in docs/agentic-system-architecture/BUILDING-BLOCKS.md:
#
#   AWS        DynamoDB condition expression on one UpdateItem
#   Azure      Cosmos ETag-based conditional write
#   GCP        Firestore transaction — read, decide, write, abort if it moved
#   Snowflake  UPDATE ... WHERE status = 'PENDING', then check the affected row count
#
# The Snowflake form looks the least like a claim primitive and is exactly as strong. A
# single UPDATE statement is atomic, and a row-store hybrid table takes a row lock for the
# duration, so two executors racing the same approval produce one UPDATE reporting one row
# and one reporting zero. The one that saw zero did not win and must not proceed. That
# check — `SQLROWCOUNT = 1` — is the entire concurrency control, and it is the line in the
# procedure below that a well-meaning edit is most likely to drop.
#
# Why a hybrid table and not a standard one: a standard Snowflake table has no row-level
# locking and no primary-key enforcement. Two concurrent UPDATEs against the same logical
# row in a standard table can both report success. The claim would then be issued twice,
# and the write tool would run twice for one human approval — which is the failure this
# entire module exists to prevent. The hybrid table is not a performance choice here.

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
# The record
#
# Both the concurrency control and the audit trail, which is why it is never deleted from
# and why it carries no retention setting of its own.
# ---------------------------------------------------------------------------

resource "snowflake_hybrid_table" "approvals" {
  database = var.database_name
  schema   = var.schema_name
  name     = "APPROVALS"
  comment  = "Approval records. Both the concurrency control and the audit trail — never expired, never deleted."

  column {
    name     = "APPROVAL_ID"
    type     = "VARCHAR(64)"
    not_null = true
  }
  column {
    name     = "CORRELATION_ID"
    type     = "VARCHAR(64)"
    not_null = true
  }
  column {
    name     = "STATUS"
    type     = "VARCHAR(16)"
    not_null = true
  }
  column {
    name     = "ACTION"
    type     = "VARCHAR(128)"
    not_null = true
  }
  column {
    name     = "ARGUMENTS"
    type     = "VARIANT"
    not_null = false
  }

  # The binding. The executor recomputes this over the arguments it was handed and
  # refuses a mismatch, so an approval for a $10 refund cannot be replayed against a
  # $10,000 one.
  column {
    name     = "ARGUMENTS_FINGERPRINT"
    type     = "VARCHAR(71)"
    not_null = true
  }
  column {
    name     = "APPROVER"
    type     = "VARCHAR(256)"
    not_null = false
  }
  column {
    name     = "APPROVER_COMMENT"
    type     = "VARCHAR(1024)"
    not_null = false
  }
  column {
    name     = "CREATED_AT"
    type     = "TIMESTAMP_NTZ"
    not_null = true
  }
  column {
    name     = "CLAIMED_AT"
    type     = "TIMESTAMP_NTZ"
    not_null = false
  }
  column {
    name     = "RESOLVED_AT"
    type     = "TIMESTAMP_NTZ"
    not_null = false
  }

  primary_key_constraint {
    name    = "PK_APPROVALS"
    columns = ["APPROVAL_ID"]
  }

  index {
    name    = "IDX_APPROVALS_CORRELATION"
    columns = ["CORRELATION_ID"]
  }
}

# ---------------------------------------------------------------------------
# Submitting a proposal
#
# Callable by the orchestrator. Writes a PENDING record and nothing else — it cannot
# approve, cannot claim, and cannot reach a write tool. This is the only part of the
# approval flow the model's own execution path touches.
# ---------------------------------------------------------------------------

resource "snowflake_procedure_sql" "submit_proposal" {
  database = var.database_name
  schema   = var.schema_name
  name     = "SUBMIT_PROPOSAL"

  return_type = "VARCHAR"
  execute_as  = "OWNER"
  comment     = "Records a write proposal as PENDING. Callable by the orchestrator; grants nothing further."

  arguments {
    arg_name      = "APPROVAL_ID"
    arg_data_type = "VARCHAR"
  }
  arguments {
    arg_name      = "CORRELATION_ID"
    arg_data_type = "VARCHAR"
  }
  arguments {
    arg_name      = "ACTION"
    arg_data_type = "VARCHAR"
  }
  arguments {
    arg_name      = "ARGUMENTS"
    arg_data_type = "VARIANT"
  }

  # The fingerprint is computed here rather than accepted as an argument. A caller that
  # supplies its own fingerprint can supply one that matches arguments it did not send,
  # which defeats the binding entirely.
  procedure_definition = <<-SQL
    BEGIN
      INSERT INTO ${var.database_name}.${var.schema_name}.APPROVALS
        (APPROVAL_ID, CORRELATION_ID, STATUS, ACTION, ARGUMENTS,
         ARGUMENTS_FINGERPRINT, CREATED_AT)
      SELECT
        :APPROVAL_ID, :CORRELATION_ID, 'PENDING', :ACTION, :ARGUMENTS,
        'sha256:' || SHA2(TO_JSON(:ARGUMENTS), 256), SYSDATE();
      RETURN 'PENDING';
    END;
  SQL
}

# ---------------------------------------------------------------------------
# Claiming an approved proposal — the single-use gate
#
# Callable by the executor and by nobody else. Two things happen in one statement:
# the record moves PENDING -> EXECUTING, and the caller learns whether it was the one
# that moved it.
#
# The stale branch is recovery, not a second chance. An executor that dies between
# claiming a record and invoking the write tool leaves the record in EXECUTING forever,
# and the execution blocked behind it. After `stale_claim_seconds` another executor may
# take it over — which is safe only because write tools are idempotent on the approval
# ID. A write tool that ignores its idempotency key turns this recovery into a double
# write, so that requirement is documented on `write_tools` in modules/tools and is not
# optional.
# ---------------------------------------------------------------------------

resource "snowflake_procedure_sql" "claim_approval" {
  database = var.database_name
  schema   = var.schema_name
  name     = "CLAIM_APPROVAL"

  return_type = "VARCHAR"
  execute_as  = "OWNER"
  comment     = "Atomically claims an APPROVED record. Returns CLAIMED, RECLAIMED or LOST. Executor only."

  arguments {
    arg_name      = "APPROVAL_ID"
    arg_data_type = "VARCHAR"
  }
  arguments {
    arg_name      = "EXPECTED_FINGERPRINT"
    arg_data_type = "VARCHAR"
  }

  # SQLROWCOUNT after the UPDATE is the concurrency control. Removing that check turns
  # two racing executors into two successful claims, which is a double write for one human
  # approval. It is guarded by tests/test_write_boundary.py.
  procedure_definition = <<-SQL
    DECLARE
      claimed INTEGER DEFAULT 0;
      prior   VARCHAR DEFAULT NULL;
    BEGIN
      SELECT STATUS INTO :prior
        FROM ${var.database_name}.${var.schema_name}.APPROVALS
       WHERE APPROVAL_ID = :APPROVAL_ID;

      IF (:prior IS NULL) THEN
        RETURN 'NOT_FOUND';
      END IF;

      UPDATE ${var.database_name}.${var.schema_name}.APPROVALS
         SET STATUS = 'EXECUTING', CLAIMED_AT = SYSDATE()
       WHERE APPROVAL_ID = :APPROVAL_ID
         AND ARGUMENTS_FINGERPRINT = :EXPECTED_FINGERPRINT
         AND (
              STATUS = 'APPROVED'
              OR (STATUS = 'EXECUTING'
                  AND CLAIMED_AT < DATEADD(second, -${var.stale_claim_seconds}, SYSDATE()))
             );

      claimed := SQLROWCOUNT;

      IF (:claimed = 1) THEN
        RETURN IFF(:prior = 'EXECUTING', 'RECLAIMED', 'CLAIMED');
      END IF;

      RETURN 'LOST';
    END;
  SQL
}

# ---------------------------------------------------------------------------
# Resolving
# ---------------------------------------------------------------------------

resource "snowflake_procedure_sql" "resolve_approval" {
  database = var.database_name
  schema   = var.schema_name
  name     = "RESOLVE_APPROVAL"

  return_type = "VARCHAR"
  execute_as  = "OWNER"
  comment     = "Marks a claimed approval SUCCEEDED or FAILED. Executor only."

  arguments {
    arg_name      = "APPROVAL_ID"
    arg_data_type = "VARCHAR"
  }
  arguments {
    arg_name      = "OUTCOME"
    arg_data_type = "VARCHAR"
  }

  procedure_definition = <<-SQL
    BEGIN
      IF (:OUTCOME NOT IN ('SUCCEEDED', 'FAILED')) THEN
        RETURN 'INVALID_OUTCOME';
      END IF;

      UPDATE ${var.database_name}.${var.schema_name}.APPROVALS
         SET STATUS = :OUTCOME, RESOLVED_AT = SYSDATE()
       WHERE APPROVAL_ID = :APPROVAL_ID
         AND STATUS = 'EXECUTING';

      RETURN IFF(SQLROWCOUNT = 1, :OUTCOME, 'LOST');
    END;
  SQL
}

# ---------------------------------------------------------------------------
# Human authorization
#
# Deliberately granted to neither the orchestrator nor the executor. A machine role that
# can move a record to APPROVED is a machine role that can approve its own proposal, which
# collapses the whole gate into a formality. This grant goes to a human role, and the
# module takes it as an input rather than creating it, because who counts as an approver
# is an organisational fact rather than an infrastructure one.
# ---------------------------------------------------------------------------

resource "snowflake_procedure_sql" "approve" {
  database = var.database_name
  schema   = var.schema_name
  name     = "APPROVE"

  return_type = "VARCHAR"
  execute_as  = "OWNER"
  comment     = "Moves PENDING to APPROVED. Granted to human approver roles only — never to the orchestrator or executor."

  arguments {
    arg_name      = "APPROVAL_ID"
    arg_data_type = "VARCHAR"
  }
  arguments {
    arg_name      = "COMMENT"
    arg_data_type = "VARCHAR"
  }

  # CURRENT_USER() rather than an argument: an approver identity the caller supplies is an
  # approver identity the caller can forge, and this column is the audit trail's answer to
  # "who authorized this".
  procedure_definition = <<-SQL
    BEGIN
      UPDATE ${var.database_name}.${var.schema_name}.APPROVALS
         SET STATUS = 'APPROVED',
             APPROVER = CURRENT_USER(),
             APPROVER_COMMENT = :COMMENT
       WHERE APPROVAL_ID = :APPROVAL_ID
         AND STATUS = 'PENDING';

      RETURN IFF(SQLROWCOUNT = 1, 'APPROVED', 'LOST');
    END;
  SQL
}

# ---------------------------------------------------------------------------
# Ownership and grants
#
# Same reasoning as modules/tools: Terraform's own role owns what it creates, and an
# owner can always execute. Ownership moves to the approval owner role so that the grants
# below are the complete list of who can do what.
# ---------------------------------------------------------------------------

locals {
  procedures = {
    submit  = "${var.database_name}.${var.schema_name}.SUBMIT_PROPOSAL(VARCHAR, VARCHAR, VARCHAR, VARIANT)"
    claim   = "${var.database_name}.${var.schema_name}.CLAIM_APPROVAL(VARCHAR, VARCHAR)"
    resolve = "${var.database_name}.${var.schema_name}.RESOLVE_APPROVAL(VARCHAR, VARCHAR)"
    approve = "${var.database_name}.${var.schema_name}.APPROVE(VARCHAR, VARCHAR)"
  }

  approvals_table = "${var.database_name}.${var.schema_name}.${snowflake_hybrid_table.approvals.name}"
}

resource "snowflake_grant_ownership" "procedures" {
  for_each = local.procedures

  account_role_name   = var.tool_owner_role
  outbound_privileges = "COPY"

  on {
    object_type = "PROCEDURE"
    object_name = each.value
  }

  depends_on = [
    snowflake_procedure_sql.submit_proposal,
    snowflake_procedure_sql.claim_approval,
    snowflake_procedure_sql.resolve_approval,
    snowflake_procedure_sql.approve,
  ]
}

# The owner needs the table privileges, because every procedure above runs as OWNER.
resource "snowflake_grant_privileges_to_account_role" "owner_table" {
  account_role_name = var.tool_owner_role
  privileges        = ["SELECT", "INSERT", "UPDATE"]

  on_schema_object {
    object_type = "TABLE"
    object_name = local.approvals_table
  }
}

# The orchestrator proposes. That is all it does here.
resource "snowflake_grant_privileges_to_account_role" "submit_to_orchestrator" {
  account_role_name = var.orchestrator_role
  privileges        = ["USAGE"]

  on_schema_object {
    object_type = "PROCEDURE"
    object_name = local.procedures["submit"]
  }

  depends_on = [snowflake_grant_ownership.procedures]
}

# The executor claims and resolves. It cannot submit and it cannot approve.
resource "snowflake_grant_privileges_to_account_role" "claim_to_executor" {
  for_each = toset(["claim", "resolve"])

  account_role_name = var.executor_role
  privileges        = ["USAGE"]

  on_schema_object {
    object_type = "PROCEDURE"
    object_name = local.procedures[each.key]
  }

  depends_on = [snowflake_grant_ownership.procedures]
}

# Humans approve. If this set is empty the gate is closed rather than open: proposals
# accumulate as PENDING and nothing can ever claim them, which is the correct direction
# for a misconfiguration to fail in.
resource "snowflake_grant_privileges_to_account_role" "approve_to_humans" {
  for_each = var.approver_roles

  account_role_name = each.value
  privileges        = ["USAGE"]

  on_schema_object {
    object_type = "PROCEDURE"
    object_name = local.procedures["approve"]
  }

  depends_on = [snowflake_grant_ownership.procedures]
}

# The auditor reads the trail and changes nothing in it.
resource "snowflake_grant_privileges_to_account_role" "auditor_read" {
  account_role_name = var.auditor_role
  privileges        = ["SELECT"]

  on_schema_object {
    object_type = "TABLE"
    object_name = local.approvals_table
  }
}
