# Model integration — Claude on Vertex AI.
#
# The AWS tree calls Bedrock. The Azure tree could not call anything, because Azure OpenAI
# requires a separately provisioned resource with its own quota approval, so that module
# is a placeholder that carries an endpoint string.
#
# GCP sits between the two. Anthropic's models are served through Vertex AI in the same
# project, with the same IAM, and no separate resource to provision — the reason handler
# authenticates as its own service account and calls the endpoint. That makes this module
# real rather than a placeholder.
#
# What it still cannot do is the enablement. Anthropic models in Model Garden require
# accepting the provider's terms once per project, through the console or the Model Garden
# API, and there is no Terraform resource for that acceptance. It is a one-time manual
# step, documented in HOW-TO-DEPLOY.md, and until it is done every model call returns 403
# with a message about the model not being enabled.
#
# That failure is at least loud. It is worth contrasting with the Azure case, where a
# missing deployment name produces a 404 that reads like a networking problem.

terraform {
  required_version = ">= 1.6"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

resource "google_project_service" "aiplatform" {
  count = var.manage_api_enablement ? 1 : 0

  project = var.project_id
  service = "aiplatform.googleapis.com"

  # Leaving the API enabled on destroy is deliberate. Disabling a project-level API
  # because one environment was torn down breaks every other environment in the project,
  # and this tree expects dev and prod to be able to share one.
  disable_on_destroy = false
}

# The reason handler calls the model as itself. No key, no secret, no rotation.
resource "google_project_iam_member" "model_user" {
  for_each = var.model_caller_members

  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = each.value
}
