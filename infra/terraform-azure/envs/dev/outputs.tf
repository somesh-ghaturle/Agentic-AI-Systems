output "dev_rg" {
  value = module.networking.resource_group_name
}

output "dev_law_id" {
  value = module.observability.log_analytics_workspace_id
}
