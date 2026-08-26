output "service_user_names" {
  description = "Created service user names, keyed by short name."
  value       = { for k, u in snowflake_service_user.this : k => u.name }
}

output "service_user_roles" {
  description = "The role each service user lands in, keyed by short name."
  value       = { for k, v in var.service_users : k => v.role }
}
