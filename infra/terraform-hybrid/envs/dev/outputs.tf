output "state_machine_arn" {
  value = module.aws_orchestrator.state_machine_arn
}

output "tool_uri" {
  value = module.gcp_tools.tool_uri
}

output "state_endpoint" {
  value = module.azure_state.state_endpoint
}

output "knowledge_index_id" {
  value = module.gcp_knowledge.index_id
}
