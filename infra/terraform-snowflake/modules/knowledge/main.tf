# Knowledge — retrieval, as a managed service rather than an index you operate
#
# The AWS tree runs OpenSearch Serverless, the Azure tree runs AI Search, the GCP tree
# runs Vertex AI Vector Search. All three are a separate service holding a copy of the
# data, which means all three have an ingestion path that can silently fall behind.
#
# Cortex Search is different in a way that matters operationally rather than technically:
# the index is defined *over a query*, and `target_lag` is a declared freshness contract
# Snowflake is responsible for meeting. There is no ingestion pipeline in this tree to
# break, because there is no copy to keep in sync — which removes the most common way a
# RAG system goes quietly stale.
#
# What it costs: the service runs a warehouse to refresh itself. A target_lag of one minute
# on a table nobody queries is a warehouse resuming every minute, forever. The default
# here is deliberately hours rather than minutes.

terraform {
  required_version = ">= 1.6"
  required_providers {
    snowflake = {
      source  = "snowflakedb/snowflake"
      version = "~> 2.20"
    }
  }
}

resource "snowflake_table" "documents" {
  database = var.database_name
  schema   = var.schema_name
  name     = "DOCUMENTS"
  comment  = "Source of truth for retrieval. The search service indexes a query over this, not a copy of it."

  # Standard rather than hybrid, unlike the approval and execution-state tables. This one
  # is scanned in bulk by the indexer and never updated a row at a time, which is the
  # access pattern columnar storage is for.
  column {
    name     = "DOC_ID"
    type     = "VARCHAR(64)"
    nullable = false
  }
  column {
    name     = "TITLE"
    type     = "VARCHAR(512)"
    nullable = true
  }
  column {
    name     = "CONTENT"
    type     = "VARCHAR(16777216)"
    nullable = false
  }
  column {
    name     = "SOURCE_URI"
    type     = "VARCHAR(2048)"
    nullable = true
  }
  column {
    name     = "UPDATED_AT"
    type     = "TIMESTAMP_NTZ"
    nullable = false
  }

  change_tracking = true
}

resource "snowflake_cortex_search_service" "main" {
  database  = var.database_name
  schema    = var.schema_name
  name      = "${var.name_prefix}_SEARCH"
  warehouse = var.warehouse_name
  comment   = "Retrieval index over DOCUMENTS. Refreshed by Snowflake against the declared target_lag."

  # The column the index is built on. Everything else in `query` is returned alongside a
  # hit rather than searched.
  on         = "CONTENT"
  attributes = ["DOC_ID", "TITLE", "SOURCE_URI"]

  target_lag      = var.target_lag
  embedding_model = var.embedding_model

  query = <<-SQL
    SELECT DOC_ID, TITLE, CONTENT, SOURCE_URI, UPDATED_AT
      FROM ${var.database_name}.${var.schema_name}.DOCUMENTS
  SQL

  depends_on = [snowflake_table.documents]
}

# Retrieval is a read path, so the orchestrator holds it directly. That is the ungated
# half of the architecture and THREAT-MODEL.md is explicit that it is the largest genuine
# gap: a prompt-injected model reads whatever this reaches. The control is what goes into
# DOCUMENTS, not who may query it.
resource "snowflake_grant_privileges_to_account_role" "search_to_orchestrator" {
  account_role_name = var.orchestrator_role
  privileges        = ["USAGE"]

  on_schema_object {
    object_type = "CORTEX SEARCH SERVICE"
    object_name = "${var.database_name}.${var.schema_name}.${snowflake_cortex_search_service.main.name}"
  }
}

resource "snowflake_grant_privileges_to_account_role" "documents_read" {
  for_each = var.document_reader_roles

  account_role_name = each.value
  privileges        = ["SELECT"]

  on_schema_object {
    object_type = "TABLE"
    object_name = "${var.database_name}.${var.schema_name}.${snowflake_table.documents.name}"
  }
}
