# Observability — the event table, and why it is created with raw SQL
#
# Every other module in this tree uses a typed provider resource. This one does not,
# because the provider has no event-table resource at v2.20 — the 143 resources it ships
# include no `snowflake_event_table`. `snowflake_execute` is the documented escape hatch,
# and using it here is a deliberate, contained exception rather than a habit.
#
# The cost of that exception is real and worth naming: `snowflake_execute` has no drift
# detection. Terraform knows it ran the statement; it does not know whether the object
# still matches. If someone drops the event table by hand, the next plan is empty and the
# next apply changes nothing. That is why `revert` is populated properly below — it is the
# only part of the resource that behaves, and getting it wrong leaves an orphaned table
# that a later apply cannot recreate because the name is taken.
#
# Traces matter more here than the equivalent on the other three clouds, because a stored
# procedure has no stdout anyone will ever read. On AWS a print lands in CloudWatch by
# accident; on Snowflake it lands nowhere. An event table is the only way a handler's own
# account of what it did survives the session that produced it.

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
  event_table = "${var.database_name}.${var.schema_name}.${var.name_prefix}_EVENTS"
}

resource "snowflake_execute" "event_table" {
  execute = "CREATE EVENT TABLE IF NOT EXISTS ${local.event_table} CHANGE_TRACKING = FALSE"
  revert  = "DROP EVENT TABLE IF EXISTS ${local.event_table}"

  # Read back what exists, so `terraform plan` at least reports the object's absence
  # rather than silently assuming it. This does not give the resource real drift
  # detection — see the header — but it turns a hand-dropped table into something visible
  # in state rather than something nobody notices until an incident needs the traces.
  query = "SHOW EVENT TABLES LIKE '${var.name_prefix}_EVENTS' IN SCHEMA ${var.database_name}.${var.schema_name}"
}

# Point the database at it. Without this the table exists and receives nothing — the
# same "declared but not wired" shape the guardrail policy exists for, one layer down.
resource "snowflake_execute" "associate_event_table" {
  execute = "ALTER DATABASE ${var.database_name} SET EVENT_TABLE = '${local.event_table}'"
  revert  = "ALTER DATABASE ${var.database_name} UNSET EVENT_TABLE"

  depends_on = [snowflake_execute.event_table]
}

# ---------------------------------------------------------------------------
# The trace table
#
# Distinct from the event table on purpose. The event table is Snowflake's own capture of
# logs and spans emitted by procedure code — schema fixed by Snowflake, retention managed
# by Snowflake. This is the agent's structured account of its own reasoning: one row per
# step, with the fields trace-level evals need.
#
# The field is `event_type`, matching AWS and Azure. The GCP tree calls it `event` because
# Cloud Logging reserves the longer name. That divergence is recorded rather than fixed —
# see infra/MODULES.md.
# ---------------------------------------------------------------------------

resource "snowflake_table" "traces" {
  database = var.database_name
  schema   = var.schema_name
  name     = "TRACES"
  comment  = "Structured agent traces. One row per step. Append-only by grant."

  column {
    name     = "TRACE_ID"
    type     = "VARCHAR(64)"
    nullable = false
  }
  column {
    name     = "CORRELATION_ID"
    type     = "VARCHAR(64)"
    nullable = false
  }
  column {
    name     = "EVENT_TYPE"
    type     = "VARCHAR(64)"
    nullable = false
  }
  column {
    name     = "STEP"
    type     = "NUMBER(10,0)"
    nullable = false
  }
  column {
    name     = "TERMINAL"
    type     = "BOOLEAN"
    nullable = false
  }
  column {
    name     = "INPUT_TOKENS"
    type     = "NUMBER(12,0)"
    nullable = true
  }
  column {
    name     = "OUTPUT_TOKENS"
    type     = "NUMBER(12,0)"
    nullable = true
  }
  column {
    name     = "LATENCY_MS"
    type     = "NUMBER(12,0)"
    nullable = true
  }
  column {
    name     = "PAYLOAD"
    type     = "VARIANT"
    nullable = true
  }
  column {
    name     = "EMITTED_AT"
    type     = "TIMESTAMP_NTZ"
    nullable = false
  }

  cluster_by = ["CORRELATION_ID"]
}

# ---------------------------------------------------------------------------
# Append-only by grant
#
# INSERT without UPDATE or DELETE. A trace that can be revised is not evidence, and the
# cheapest way to make that true is to never grant the privilege that would allow it.
# ---------------------------------------------------------------------------

resource "snowflake_grant_privileges_to_account_role" "trace_writers" {
  for_each = var.trace_writer_roles

  account_role_name = each.value
  privileges        = ["INSERT"]

  on_schema_object {
    object_type = "TABLE"
    object_name = "${var.database_name}.${var.schema_name}.${snowflake_table.traces.name}"
  }
}

resource "snowflake_grant_privileges_to_account_role" "trace_readers" {
  for_each = var.trace_reader_roles

  account_role_name = each.value
  privileges        = ["SELECT"]

  on_schema_object {
    object_type = "TABLE"
    object_name = "${var.database_name}.${var.schema_name}.${snowflake_table.traces.name}"
  }
}
