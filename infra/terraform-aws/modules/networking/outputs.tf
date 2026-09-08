output "handler_security_group_id" {
  description = "Attach every VPC-attached handler to this. It permits 443 to the endpoints and nothing else."
  value       = aws_security_group.handlers.id
}

output "endpoint_security_group_id" {
  description = "For VPC endpoints declared outside this module — the knowledge collection's, which lives with the collection it serves."
  value       = aws_security_group.endpoints.id
}

output "interface_endpoint_ids" {
  description = "Endpoint id by service name, for assertions and for debugging a call that hangs."
  value       = { for service, endpoint in aws_vpc_endpoint.interface : service => endpoint.id }
}
