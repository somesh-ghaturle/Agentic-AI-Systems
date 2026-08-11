output "read_tool_urls" {
  description = <<-DESC
    Invocation URLs for read tools only — what the orchestrator is given.

    Write tool URLs are deliberately absent from this output. The orchestrator's workflow
    is built from this map, so a write tool has no address to call even before Entra
    refuses it a token. Same reasoning as the AWS side passing only read_tool_arns into
    the state machine's IAM policy.
  DESC

  value = {
    for name, app in azurerm_linux_function_app.tool : name => "https://${app.default_hostname}/api/${name}"
    if var.tools[name].access == "read"
  }
}

output "write_tool_urls" {
  description = <<-DESC
    Invocation URLs for write tools — consumed ONLY by the approval executor.

    Anything else taking a dependency on this output is a design error worth stopping to
    examine: it means something other than the executor intends to call a write tool.
  DESC

  value = {
    for name, app in azurerm_linux_function_app.tool : name => "https://${app.default_hostname}/api/${name}"
    if var.tools[name].access == "write"
  }
}

output "tool_audiences" {
  description = <<-DESC
    Map of tool name to the audience a caller must request a token for. The executor and
    orchestrator need these to acquire tokens via their managed identities.
  DESC

  value = { for name, app in azuread_application.tool : name => "api://${var.name_prefix}-tool-${name}" }
}

output "function_app_names" {
  description = "All tool function app names, for diagnostic settings and alarm scoping."
  value       = { for name, app in azurerm_linux_function_app.tool : name => app.name }
}

output "function_app_ids" {
  description = "All tool function app resource IDs, for diagnostic settings."
  value       = { for name, app in azurerm_linux_function_app.tool : name => app.id }
}

output "storage_account_id" {
  description = "Tools storage account ID, for diagnostic settings and private endpoints."
  value       = azurerm_storage_account.tools.id
}
