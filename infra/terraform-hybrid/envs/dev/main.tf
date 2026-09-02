locals {
  name_prefix = "agentic-hybrid-dev"
  definition = jsonencode({
    Comment = "Hybrid POC; tool and state endpoints are supplied as input."
    StartAt = "InvokeTool"
    States = {
      InvokeTool = {
        Type = "Pass"
        Result = {
          status = "not configured"
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
  tool_endpoint    = module.gcp_tools.tool_uri
  state_endpoint   = module.azure_state.state_endpoint
  enable_resources = var.enable_resources
}
