# Archive — where traces go to stop costing warehouse money
#
# The trace table in modules/observability is the live record: clustered, queried, and
# billed as active storage. This is the cold half. The split exists because trace volume
# from an agent is dominated by rows nobody will ever read again, and keeping them in a
# clustered table means paying to re-cluster data whose only remaining job is to exist
# if an auditor asks.
#
# The internal stage rather than an external bucket is deliberate and is the one place
# this tree is genuinely simpler than the other three. On AWS this module is an S3 bucket
# with a lifecycle policy, a KMS grant and a bucket policy; on Azure a storage account
# with its own network rules. Here the data never leaves the account, so there is no
# cross-service identity to arrange and no second encryption boundary to reason about.

terraform {
  required_version = ">= 1.6"
  required_providers {
    snowflake = {
      source  = "snowflakedb/snowflake"
      version = "~> 2.20"
    }
  }
}

resource "snowflake_table" "archived_traces" {
  database = var.database_name
  schema   = var.schema_name
  name     = "ARCHIVED_TRACES"
  comment  = "Cold traces. Written by the archival task, read only during an investigation."

  # A transient table would be the right answer here and the provider does not offer one:
  # `snowflake_table` has no `is_transient` attribute at v2.20. Transient tables carry no
  # fail-safe, and fail-safe is seven days of storage Snowflake bills for, cannot be
  # queried, and will not disable — disaster recovery for Snowflake's benefit rather than
  # yours, paid for twice on a table that is already a copy of an append-only source.
  #
  # Since the attribute does not exist, the cost is managed with the only lever that does:
  # the Time Travel window below, kept short. If the provider gains `is_transient`, this
  # table should take it.

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
    name     = "PAYLOAD"
    type     = "VARIANT"
    nullable = true
  }
  column {
    name     = "EMITTED_AT"
    type     = "TIMESTAMP_NTZ"
    nullable = false
  }
  column {
    name     = "ARCHIVED_AT"
    type     = "TIMESTAMP_NTZ"
    nullable = false
  }

  data_retention_time_in_days = var.archive_retention_days
}

# An internal stage for anything leaving Snowflake entirely — a regulator's export, a
# handover to a system that is not this one. Server-side encrypted rather than
# client-side: client-side would need a key held outside Snowflake, which is a credential,
# and this tree does not have one. See docs/SECRETS-ROTATION.md.
resource "snowflake_stage_internal" "exports" {
  database = var.database_name
  schema   = var.schema_name
  name     = "${var.name_prefix}_EXPORTS"
  comment  = "Internal stage for trace exports leaving the account."

  # Server-side rather than full client-side encryption. SNOWFLAKE_FULL would encrypt with
  # a key the client holds, and a key the client holds is a credential this tree has
  # deliberately not created — see modules/identity and docs/SECRETS-ROTATION.md.
  encryption {
    snowflake_sse {}
  }
}

resource "snowflake_grant_privileges_to_account_role" "archive_read" {
  for_each = var.reader_roles

  account_role_name = each.value
  privileges        = ["SELECT"]

  on_schema_object {
    object_type = "TABLE"
    object_name = "${var.database_name}.${var.schema_name}.${snowflake_table.archived_traces.name}"
  }
}
