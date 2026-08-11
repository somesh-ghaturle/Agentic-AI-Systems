output "identities" {
  description = <<-DESC
    Map of logical name to the three IDs each consumer needs:

      principal_id — the object ID, what you grant RBAC roles and app roles to
      client_id    — what a workload presents when requesting a token
      id           — the ARM resource ID, what you attach to a Function App or Logic App

    Consumers should index this map by name rather than taking a flat list, so that a
    misspelled identity fails at plan time instead of silently attaching the wrong one.
  DESC

  value = {
    for name, identity in azurerm_user_assigned_identity.this : name => {
      principal_id = identity.principal_id
      client_id    = identity.client_id
      id           = identity.id
    }
  }
}
