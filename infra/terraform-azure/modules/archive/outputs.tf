output "container_name" {
  description = "Container holding trace archives."
  value       = azurerm_storage_container.archive.name
}

output "storage_account_name" {
  description = "Archive storage account name. Handlers resolve the endpoint from this."
  value       = azurerm_storage_account.archive_sa.name
}

output "storage_account_id" {
  description = "Archive storage account resource ID, for diagnostic settings."
  value       = azurerm_storage_account.archive_sa.id
}

output "immutability_locked" {
  description = <<-DESC
    Whether the archive is under a locked WORM policy. Surfaced because it changes what
    `terraform destroy` can do: when true, the container and account survive a destroy
    until every blob has aged past its retention period.
  DESC
  value       = var.immutability_period_days != null && var.lock_immutability_policy
}
