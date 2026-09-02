resource "google_vertex_ai_index" "knowledge" {
  count = var.enable_resources ? 1 : 0

  project      = var.project_id
  region       = var.region
  display_name = "${var.name_prefix}-knowledge"
  description  = "Hybrid POC knowledge index; data ingestion is intentionally out of scope."

  metadata {
    contents_delta_uri = "gs://${var.project_id}-hybrid-poc/index"

    config {
      dimensions                  = var.dimensions
      approximate_neighbors_count = 100
      distance_measure_type       = "SQUARED_L2_DISTANCE"
    }
  }
}
