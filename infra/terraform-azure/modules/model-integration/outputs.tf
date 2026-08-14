output "azure_openai_endpoint" {
  description = "Endpoint the reasoning tool calls — the created account's, or the one passed in. Consumers do not need to know which mode the module is in."
  value       = local.endpoint
}

output "model_deployment_name" {
  description = "Deployment name the reasoning tool targets."
  value       = local.deployment_name
}

output "azure_openai_key_secret_name" {
  description = "Key Vault secret name holding a model API key, for a bring-your-own account that cannot use token auth. Empty when the model layer authenticates by managed identity, which is the intended state."
  value       = var.azure_openai_key_secret_name
}

output "account_id" {
  description = "ARM resource ID of the created account, or null in bring-your-own mode."
  value       = local.create ? azurerm_cognitive_account.openai[0].id : null
}

output "identity_principal_id" {
  description = "The account's own system-assigned identity, for granting it access to a customer-managed key."
  value       = local.create ? azurerm_cognitive_account.openai[0].identity[0].principal_id : null
}

output "content_filter_name" {
  description = <<-DESC
    Name of the Responsible AI policy attached to the deployment, or null.

    Null is worth noticing rather than assuming away: it means either the account is managed
    out of band (in which case Terraform asserts nothing about whether a filter exists) or
    the filter was disabled. The write boundary does not depend on this, but the mitigation
    layer terraform-aws/modules/security provides has no counterpart while it reads null.
  DESC
  value       = local.create && var.create_content_filter ? azurerm_cognitive_account_rai_policy.guardrail[0].name : null
}

output "local_auth_enabled" {
  description = "Whether API keys are live on the model account. Surfaced so it can be asserted in review: with this true, the role assignments in this module are advisory."
  value       = local.create ? azurerm_cognitive_account.openai[0].local_auth_enabled : null
}
