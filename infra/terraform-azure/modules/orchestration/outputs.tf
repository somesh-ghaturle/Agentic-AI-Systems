output "logic_app_workflow_name" {
  description = "Workflow name, for alert scoping and CLI use."
  value       = azurerm_logic_app_workflow.orchestrator.name
}

output "logic_app_workflow_id" {
  description = "Workflow resource ID."
  value       = azurerm_logic_app_workflow.orchestrator.id
}

output "trigger_url" {
  description = <<-DESC
    The endpoint that starts a run.

    This is a SAS-signed URL — the signature is the credential, so it is sensitive in a
    way the other URLs in this stack are not. Everything else here is protected by Easy
    Auth and a token; this one is protected by the secret in the query string.

    That asymmetry is a property of Logic App request triggers, not a choice made here.
    Put an API Management or Front Door layer in front of it before exposing it to
    anything you do not control.
  DESC
  value       = azurerm_logic_app_trigger_http_request.start.callback_url
  sensitive   = true
}
