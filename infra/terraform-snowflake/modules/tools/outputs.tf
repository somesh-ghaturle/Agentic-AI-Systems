output "read_tool_signatures" {
  description = "Fully qualified read-tool signatures, keyed by tool name."
  value       = local.read_signatures
}

output "write_tool_signatures" {
  description = "Fully qualified write-tool signatures, keyed by tool name. Callable only by the executor role."
  value       = local.write_signatures
}

output "write_tool_names" {
  description = "Write-tool procedure names, for the approval executor's allow-list."
  value       = sort([for k, v in var.write_tools : upper(k)])
}
