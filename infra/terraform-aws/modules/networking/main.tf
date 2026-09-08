# Private egress for the handlers — ENVIRONMENT-ENGINEERING.md section 2
#
# This module exists because of a gap the tree carried for a long time and stated plainly
# before it was closed: prod and staging lock the knowledge collection to a VPC endpoint,
# and nothing put a handler inside the VPC to use it. The strict setting was declared
# rather than exercised. What follows is the other half.
#
# IT DOES NOT CREATE A NETWORK. The VPC and the subnets are inputs, the same way
# `modules/knowledge` already takes them, because an organisation running this has a VPC
# with routing, flow logs and an IPAM plan already, and a reference deployment that invents
# a second one is not the shape anyone adopts. What is created here is the part that is
# specific to these handlers: two security groups and the endpoints they talk to.
#
# NO NAT GATEWAY, DELIBERATELY. A Lambda in a private subnet has no route to the internet,
# and the usual fix is a NAT gateway at roughly $32 a month per availability zone plus
# $0.045 per GB — the GB being every Bedrock response the agent reads. Interface endpoints
# cost about $7 per month per AZ each and keep the traffic off the public internet
# entirely, which is both the cheaper answer at this volume and the stronger one. The
# trade is that a service reached by a handler and missing from `interface_services` fails
# with a timeout rather than a permission error, which is why that list is a variable with
# the handlers' actual call list as its default.

terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.58"
    }
  }
}

data "aws_region" "current" {}

# Gateway endpoints attach to route tables, not subnets, and the route tables are a
# property of the network we were handed rather than something to ask the caller to
# restate. Looking them up per subnet also means a caller who passes subnets from two
# different route tables gets both, which is the case a single `route_table_id` variable
# would silently get wrong.
data "aws_route_table" "handler_subnet" {
  for_each = toset(var.subnet_ids)

  subnet_id = each.value
}

# ---------------------------------------------------------------------------
# Two security groups, because one would be a cycle
#
# The handlers need egress to the endpoints; the endpoints need ingress from the handlers.
# Expressed as a single self-referencing group that is a rule nobody can read six months
# later, and expressed as two groups referring to each other inline it is a Terraform
# cycle. Separate rule resources are what make the pair declarable at all, and they are
# also what makes the intent legible: exactly one port, in exactly one direction, between
# exactly these two groups.
# ---------------------------------------------------------------------------

resource "aws_security_group" "handlers" {
  name        = "${var.name_prefix}-handlers"
  description = "Lambda handlers. Egress to the VPC endpoints only."
  vpc_id      = var.vpc_id

  tags = merge(var.tags, {
    Component = "handler-network"
    Layer     = "networking"
  })
}

resource "aws_security_group" "endpoints" {
  name        = "${var.name_prefix}-endpoints"
  description = "Interface VPC endpoints. Ingress from the handlers only."
  vpc_id      = var.vpc_id

  tags = merge(var.tags, {
    Component = "endpoint-network"
    Layer     = "networking"
  })
}

# No egress rule on the handler group beyond this one. That is the point: a handler that
# gains a call to a service with no endpoint here fails closed, in its own environment,
# rather than reaching the internet from production because the group allowed 0.0.0.0/0.
resource "aws_vpc_security_group_egress_rule" "handlers_to_endpoints" {
  security_group_id = aws_security_group.handlers.id
  description       = "HTTPS to the interface endpoints"

  referenced_security_group_id = aws_security_group.endpoints.id
  ip_protocol                  = "tcp"
  from_port                    = 443
  to_port                      = 443
}

resource "aws_vpc_security_group_ingress_rule" "endpoints_from_handlers" {
  security_group_id = aws_security_group.endpoints.id
  description       = "HTTPS from the handlers"

  referenced_security_group_id = aws_security_group.handlers.id
  ip_protocol                  = "tcp"
  from_port                    = 443
  to_port                      = 443
}

# ---------------------------------------------------------------------------
# The endpoints themselves
# ---------------------------------------------------------------------------

# DynamoDB is a gateway endpoint: no ENI, no hourly charge, and it works by adding a
# prefix-list route rather than by resolving a private IP. Free is the whole argument —
# there is no reason to pay interface-endpoint rates for the state store.
resource "aws_vpc_endpoint" "dynamodb" {
  vpc_id            = var.vpc_id
  service_name      = "com.amazonaws.${data.aws_region.current.region}.dynamodb"
  vpc_endpoint_type = "Gateway"

  route_table_ids = distinct([for rt in data.aws_route_table.handler_subnet : rt.route_table_id])

  tags = merge(var.tags, {
    Component = "dynamodb-endpoint"
    Layer     = "networking"
  })
}

# `private_dns_enabled` is what makes this transparent to the handlers: without it the SDK
# still resolves the public name, the call leaves the VPC, finds no route, and hangs until
# the function's timeout. The endpoint would sit there healthy and unused — the same
# failure the Azure tree documents for a private endpoint with no private DNS zone.
resource "aws_vpc_endpoint" "interface" {
  for_each = toset(var.interface_services)

  vpc_id            = var.vpc_id
  service_name      = "com.amazonaws.${data.aws_region.current.region}.${each.value}"
  vpc_endpoint_type = "Interface"

  subnet_ids          = var.subnet_ids
  security_group_ids  = [aws_security_group.endpoints.id]
  private_dns_enabled = true

  tags = merge(var.tags, {
    Component = "${each.value}-endpoint"
    Layer     = "networking"
  })
}
