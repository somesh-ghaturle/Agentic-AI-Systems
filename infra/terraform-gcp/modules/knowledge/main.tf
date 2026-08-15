# Knowledge layer — Vertex AI Vector Search.
#
# The retrieve tool searches this index. The property that matters is not that retrieval
# works; it is that retrieval is tenant-scoped, and that the scoping happens *during* the
# search rather than after it.
#
# From terraform-aws/ARCHITECTURE.md section 7:
#
#   "Retrieval is tenant-scoped — enforced by CODE: filter inside the kNN clause, not
#    beside it. If it breaks: ranks other tenants' documents first, then hides them."
#
# On Vector Search the mechanism is a **restrict**. Each datapoint carries namespaces, and
# a query supplies `restricts` that the ANN search honours while traversing the index. A
# query that instead retrieves 100 neighbours and drops the ones belonging to other
# tenants returns the same shape of answer and is wrong in the same way the AWS version is
# wrong: the tenant's own best match may never have been in the 100.
#
# Terraform cannot enforce that. The index below is capable of it either way. This comment
# is here because the capability and the correct use of it are different things, and the
# module that provides the first should say so.

terraform {
  required_version = ">= 1.6"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.44"
    }
  }
}

# Vector Search reads its initial contents from GCS. Even a stream-updated index needs a
# delta URI at creation time, and it must point at a prefix that exists.
resource "google_storage_bucket" "corpus" {
  project = var.project_id

  name     = "${var.name_prefix}-corpus"
  location = var.location

  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  dynamic "encryption" {
    for_each = var.kms_key_id == null ? [] : [var.kms_key_id]
    content {
      default_kms_key_name = encryption.value
    }
  }

  labels = var.labels
}

# The index expects to find at least an empty prefix here. Creating the placeholder means
# a fresh apply succeeds without someone having to remember to upload embeddings first.
resource "google_storage_bucket_object" "corpus_placeholder" {
  name    = "${var.contents_prefix}/.keep"
  bucket  = google_storage_bucket.corpus.name
  content = "Vector Search reads embeddings from this prefix. See HOW-TO-DEPLOY.md.\n"
}

resource "google_vertex_ai_index" "corpus" {
  project = var.project_id
  region  = var.location

  display_name = "${var.name_prefix}-corpus"
  description  = "Agentic system retrieval corpus. Tenant scoping is applied as a namespace restrict during search — see modules/knowledge/main.tf."

  metadata {
    contents_delta_uri = "${google_storage_bucket.corpus.url}/${var.contents_prefix}"

    config {
      dimensions = var.dimensions

      # How many neighbours the ANN search considers before returning. Too low and a
      # heavily restricted query — one tenant's slice of a large corpus — comes back
      # short, because the restrict is applied to candidates the search already chose.
      # This is the parameter that makes a correct restrict *behave* like a post-filter.
      approximate_neighbors_count = var.approximate_neighbors_count

      distance_measure_type = var.distance_measure_type

      algorithm_config {
        tree_ah_config {
          leaf_node_embedding_count    = var.leaf_node_embedding_count
          leaf_nodes_to_search_percent = var.leaf_nodes_to_search_percent
        }
      }
    }
  }

  # STREAM_UPDATE lets the corpus be written incrementally. BATCH_UPDATE is cheaper and
  # rebuilds from GCS on a schedule; it is the right choice when the corpus changes daily
  # rather than continuously.
  index_update_method = var.index_update_method

  labels = var.labels

  depends_on = [google_storage_bucket_object.corpus_placeholder]
}

resource "google_vertex_ai_index_endpoint" "corpus" {
  project = var.project_id
  region  = var.location

  display_name = "${var.name_prefix}-corpus-endpoint"
  description  = "Serving endpoint for the retrieval corpus."

  # Public endpoint keeps this tree free of VPC peering, which would otherwise be the
  # single largest piece of infrastructure here and has nothing to do with agentic AI.
  # The endpoint still requires IAM to query; public means reachable, not open.
  public_endpoint_enabled = true

  labels = var.labels
}

# Deploying the index to the endpoint is what makes it queryable, and it is what costs
# money: the replicas below run continuously whether or not anything queries them. This is
# the most expensive resource in the tree by a wide margin.
resource "google_vertex_ai_index_endpoint_deployed_index" "corpus" {
  index_endpoint = google_vertex_ai_index_endpoint.corpus.id
  index          = google_vertex_ai_index.corpus.id

  # Must be unique within the endpoint and match `[a-z][a-z0-9_]*`. Hyphens are rejected,
  # which is why this underscores the prefix rather than using it verbatim.
  deployed_index_id = "${replace(var.name_prefix, "-", "_")}_corpus"
  display_name      = "${var.name_prefix}-corpus"

  dedicated_resources {
    machine_spec {
      machine_type = var.machine_type
    }

    min_replica_count = var.min_replica_count
    max_replica_count = var.max_replica_count
  }
}

# The retrieve tool queries the index. This grant belongs to the *tool's* service account,
# not the orchestrator's — the orchestrator never talks to Vector Search directly.
#
# The AWS tree makes the same point about OpenSearch Serverless data access policies, and
# it is worth repeating because the mistake is natural: the orchestrator is the thing that
# "does retrieval" from a reader's point of view, so granting it access feels right and
# leaves the retrieve tool broken.
resource "google_project_iam_member" "index_querier" {
  for_each = var.querier_members

  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = each.value
}
