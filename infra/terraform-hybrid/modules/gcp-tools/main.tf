resource "google_cloudfunctions2_function" "tool" {
  count = var.enable_resources ? 1 : 0

  project  = var.project_id
  location = var.location
  name     = "${var.name_prefix}-tool"

  build_config {
    runtime     = "python312"
    entry_point = "handle"
    source {
      storage_source {
        bucket = var.source_bucket
        object = var.source_object
      }
    }
  }

  service_config {
    max_instance_count             = 2
    available_memory               = "256M"
    timeout_seconds                = 30
    ingress_settings               = "ALLOW_INTERNAL_ONLY"
    all_traffic_on_latest_revision = true
  }
}
