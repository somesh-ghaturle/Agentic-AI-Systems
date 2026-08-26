# State — the database, the schemas, the warehouse, and the execution record
#
# This module owns more than its AWS and GCP counterparts, and the reason is structural
# rather than stylistic. On the other three clouds every module provisions its own
# top-level containers: an S3 bucket, a Cosmos account, a Firestore database. Snowflake
# has one namespace tree — DATABASE > SCHEMA > object — and every other module in this
# tree writes into it. Splitting ownership of that tree across nine modules produces nine
# modules that must be applied in a fixed order and cannot be destroyed independently.
#
# So the namespace lives here, and every other module takes `database` and `schema` as
# inputs. That is the same trade `terraform-gcp/modules/state` makes with its Firestore
# database, one level higher up.
#
# The schema split is the write boundary's foundation, not organisation:
#
#   APP    execution state and approvals — written by the agent's own path
#   TOOLS  the read and write procedures — see modules/tools for who may call which
#   AUDIT  traces and the archive — append-only by grant, never updated
#
# A schema is the smallest unit Snowflake will grant FUTURE privileges on. Keeping write
# procedures in their own schema is what makes "the orchestrator holds nothing in TOOLS"
# a statement about a container rather than about a list of names that grows.

terraform {
  required_version = ">= 1.6"
  required_providers {
    snowflake = {
      source  = "snowflakedb/snowflake"
      version = "~> 2.20"
    }
  }
}

resource "snowflake_database" "main" {
  name    = var.database_name
  comment = "Agentic system — ${var.name_prefix}"

  # Time Travel. The approvals table lives in here, and a mistaken UPDATE against an audit
  # trail is exactly the case Time Travel exists for. One day in dev, the Enterprise
  # maximum in prod.
  data_retention_time_in_days = var.data_retention_time_in_days

  # Snowflake creates a PUBLIC schema on every database, owned by the database owner and
  # granted to PUBLIC. It is a schema every role in the account can create objects in,
  # which is not a thing this stack wants sitting inside its namespace.
  drop_public_schema_on_creation = true
}

# ---------------------------------------------------------------------------
# Schemas
#
# `with_managed_access` is the setting that matters here and it is easy to miss.
#
# Without it, the owner of an object may grant privileges on that object to anyone. A
# write procedure's owner could hand USAGE to the orchestrator role, and no policy in
# this tree would see it — the grant is made by an object owner, not by an admin, and it
# never appears in this Terraform state at all.
#
# With managed access, only the schema owner may grant on objects in the schema. Object
# owners keep ownership and lose the ability to delegate it. That converts "nobody has
# granted the orchestrator USAGE on a write procedure" from a fact about the current
# moment into a property of the container.
# ---------------------------------------------------------------------------

resource "snowflake_schema" "app" {
  database = snowflake_database.main.name
  name     = "APP"
  comment  = "Execution state and approval records."

  with_managed_access         = true
  data_retention_time_in_days = var.data_retention_time_in_days
}

resource "snowflake_schema" "tools" {
  database = snowflake_database.main.name
  name     = "TOOLS"
  comment  = "Read and write tool procedures. The write boundary is drawn inside this schema."

  # Non-negotiable here, whatever the caller passes elsewhere. This is the schema whose
  # grants are the write boundary; letting a procedure owner delegate USAGE on their own
  # procedure is the one failure this design cannot survive.
  with_managed_access         = true
  data_retention_time_in_days = var.data_retention_time_in_days
}

resource "snowflake_schema" "audit" {
  database = snowflake_database.main.name
  name     = "AUDIT"
  comment  = "Traces and archived executions. Append-only by grant."

  with_managed_access         = true
  data_retention_time_in_days = var.data_retention_time_in_days
}

# ---------------------------------------------------------------------------
# Warehouse
#
# Snowflake bills compute by the second while a warehouse is resumed, so an agent that
# polls is an agent that bills. `auto_suspend` is the control, and 60 seconds is chosen
# rather than inherited: the default is 600, and ten minutes of idle warehouse after every
# short agent run is the single largest avoidable cost in this stack.
# ---------------------------------------------------------------------------

resource "snowflake_warehouse" "main" {
  name           = "${var.name_prefix}_WH"
  warehouse_size = var.warehouse_size
  comment        = "Agentic system compute — ${var.name_prefix}"

  auto_suspend        = var.auto_suspend_seconds
  auto_resume         = "true"
  initially_suspended = true

  # A runaway query in an agent loop is a bill, not an outage. This bounds it.
  statement_timeout_in_seconds        = var.statement_timeout_in_seconds
  statement_queued_timeout_in_seconds = var.statement_queued_timeout_in_seconds

  max_cluster_count = var.max_cluster_count
  min_cluster_count = 1
  scaling_policy    = "STANDARD"
}

# ---------------------------------------------------------------------------
# Execution state
#
# A hybrid table rather than a standard one. Agent execution state is read and written
# one row at a time by key, which is the access pattern a columnar micro-partition store
# is worst at: a standard table turns "read this execution's state" into a partition scan
# and "update it" into a rewrite. Hybrid tables are row-stored with real primary-key
# enforcement and single-row latency.
#
# The primary key is doing correctness work, not just lookup work — it is what makes a
# second writer for the same execution a constraint violation instead of a duplicate row.
# ---------------------------------------------------------------------------

resource "snowflake_hybrid_table" "execution_state" {
  database = snowflake_database.main.name
  schema   = snowflake_schema.app.name
  name     = "EXECUTION_STATE"
  comment  = "Per-execution agent state. Row-stored: single-key reads and writes."

  column {
    name     = "EXECUTION_ID"
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
    type     = "VARCHAR(32)"
    not_null = true
  }
  column {
    name     = "STEP"
    type     = "NUMBER(10,0)"
    not_null = true
  }
  column {
    name     = "PAYLOAD"
    type     = "VARIANT"
    not_null = false
  }
  column {
    name     = "CREATED_AT"
    type     = "TIMESTAMP_NTZ"
    not_null = true
  }
  column {
    name     = "UPDATED_AT"
    type     = "TIMESTAMP_NTZ"
    not_null = true
  }

  primary_key_constraint {
    name    = "PK_EXECUTION_STATE"
    columns = ["EXECUTION_ID"]
  }

  # Reconstructing "everything that happened under this correlation ID" is the first thing
  # anyone does in an incident. Without an index that is a full scan of a row store, which
  # is the one thing row stores are bad at.
  index {
    name    = "IDX_EXECUTION_STATE_CORRELATION"
    columns = ["CORRELATION_ID"]
  }
}
