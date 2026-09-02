locals {
  name_prefix = "agentic-hybrid-dev"

  # The root is the only layer that sees every provider, so it resolves the
  # cross-cloud endpoints and embeds them in the state machine definition. Both
  # are null while `enable_resources` is false, which is what makes the disabled
  # tree still express the topology: the wiring is visible in the plan even when
  # nothing is created.
  definition = jsonencode({
    Comment = "Hybrid POC; the tool and state endpoints are resolved at plan time."
    StartAt = "InvokeTool"
    States = {
      InvokeTool = {
        Type = "Pass"
        Result = {
          status         = var.enable_resources ? "configured" : "not configured"
          tool_endpoint  = module.gcp_tools.tool_uri
          state_endpoint = module.azure_state.state_endpoint
        }
        End = true
      }
    }
  })
}

module "gcp_tools" {
  source           = "../../modules/gcp-tools"
  project_id       = var.gcp_project_id
  location         = var.gcp_region
  name_prefix      = local.name_prefix
  enable_resources = var.enable_resources
}

module "azure_state" {
  source              = "../../modules/azure-state"
  resource_group_name = var.azure_resource_group_name
  location            = var.azure_location
  name_prefix         = "agentichybridd"
  enable_resources    = var.enable_resources
}

module "gcp_knowledge" {
  source           = "../../modules/gcp-knowledge"
  project_id       = var.gcp_project_id
  region           = var.gcp_region
  name_prefix      = local.name_prefix
  enable_resources = var.enable_resources
}

module "aws_orchestrator" {
  source           = "../../modules/aws-orchestrator"
  name_prefix      = local.name_prefix
  definition       = local.definition
  enable_resources = var.enable_resources
}
