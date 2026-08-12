variable "project_id" {
  description = "GCP project."
  type        = string
}

variable "name_prefix" {
  description = "Prefix for resource names. The corpus bucket name derives from this and must be globally unique."
  type        = string
}

variable "location" {
  description = "Region for the index, endpoint, and corpus bucket. Vector Search is not available in every region."
  type        = string
}

variable "kms_key_id" {
  description = "Customer-managed key for the corpus bucket."
  type        = string
  default     = null
}

variable "contents_prefix" {
  description = "Prefix within the corpus bucket holding embedding files."
  type        = string
  default     = "embeddings"
}

variable "dimensions" {
  description = "Embedding dimensionality. Must match the embedding model the retrieve tool uses — 768 for text-embedding-004, 3072 for gemini-embedding-001. A mismatch is accepted at create time and fails on every query."
  type        = number
  default     = 768
}

variable "approximate_neighbors_count" {
  description = "Candidate neighbours the ANN search considers. Raise it when queries carry restrictive namespace filters, or a tenant-scoped query returns fewer results than it should."
  type        = number
  default     = 150
}

variable "distance_measure_type" {
  description = "DOT_PRODUCT_DISTANCE, COSINE_DISTANCE, SQUARED_L2_DISTANCE, or L1_DISTANCE. Must match how the embeddings were produced."
  type        = string
  default     = "DOT_PRODUCT_DISTANCE"

  validation {
    condition     = contains(["DOT_PRODUCT_DISTANCE", "COSINE_DISTANCE", "SQUARED_L2_DISTANCE", "L1_DISTANCE"], var.distance_measure_type)
    error_message = "distance_measure_type must be one of DOT_PRODUCT_DISTANCE, COSINE_DISTANCE, SQUARED_L2_DISTANCE, L1_DISTANCE."
  }
}

variable "leaf_node_embedding_count" {
  description = "Embeddings per leaf node in the tree-AH index."
  type        = number
  default     = 500
}

variable "leaf_nodes_to_search_percent" {
  description = "Percentage of leaf nodes searched per query. Higher is more accurate and slower."
  type        = number
  default     = 7
}

variable "index_update_method" {
  description = "STREAM_UPDATE for incremental writes, BATCH_UPDATE for periodic rebuilds from GCS."
  type        = string
  default     = "STREAM_UPDATE"

  validation {
    condition     = contains(["STREAM_UPDATE", "BATCH_UPDATE"], var.index_update_method)
    error_message = "index_update_method must be STREAM_UPDATE or BATCH_UPDATE."
  }
}

variable "machine_type" {
  description = "Machine type for the deployed index replicas. These run continuously."
  type        = string
  default     = "e2-standard-2"
}

variable "min_replica_count" {
  description = "Minimum serving replicas. Cannot be zero — a deployed index has no scale-to-zero, which is why this module is the tree's largest standing cost."
  type        = number
  default     = 1
}

variable "max_replica_count" {
  description = "Maximum serving replicas."
  type        = number
  default     = 1
}

variable "querier_members" {
  description = "Principals granted roles/aiplatform.user, keyed by name. This should be the retrieve tool's service account, not the orchestrator's."
  type        = map(string)
  default     = {}
}

variable "labels" {
  description = "Labels applied to every resource in this module that supports them."
  type        = map(string)
  default     = {}
}
