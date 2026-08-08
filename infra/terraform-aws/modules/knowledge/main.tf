# Knowledge memory — BUILDING-BLOCKS.md §3, PRODUCTION-PRINCIPLES.md "Context and RAG design"
#
# The semantic corpus and its retrieval machinery. A read path with its own latency and
# cost profile, cacheable independently of the model layer.
#
# OpenSearch Serverless is chosen here for one architectural reason beyond managed
# convenience: it does hybrid search natively. Semantic search alone misses exact terms —
# error codes, product IDs, names — and the doc calls fixing that "a whole class of misses."
# pgvector on RDS is the reasonable alternative when you already run Postgres.
#
# TENANT ISOLATION IS ENFORCED AT QUERY TIME, NOT HERE. Metadata filtering before semantic
# search is what prevents cross-tenant leakage. Terraform gives you the collection and the
# network boundary; the filter is application code.

terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

resource "aws_opensearchserverless_collection" "knowledge" {
  name = "${var.name_prefix}-knowledge"
  type = "VECTORSEARCH"

  tags = merge(var.tags, {
    Component = "knowledge-memory"
    Layer     = "memory-and-state"
  })

  # Collections fail to create without their policies in place first.
  depends_on = [
    aws_opensearchserverless_security_policy.encryption,
    aws_opensearchserverless_security_policy.network,
  ]
}

resource "aws_opensearchserverless_security_policy" "encryption" {
  name = "${var.name_prefix}-knowledge-enc"
  type = "encryption"

  policy = jsonencode({
    Rules = [{
      Resource     = ["collection/${var.name_prefix}-knowledge"]
      ResourceType = "collection"
    }]
    AWSOwnedKey = var.kms_key_arn == null
    KmsARN      = var.kms_key_arn
  })
}

# Public access is the default in many examples and is wrong for a corpus that may hold
# customer documents. VPC-only is the sane posture; the variable exists so a sandbox can
# opt out deliberately rather than by omission.
resource "aws_opensearchserverless_security_policy" "network" {
  name = "${var.name_prefix}-knowledge-net"
  type = "network"

  policy = jsonencode([{
    Rules = [{
      Resource     = ["collection/${var.name_prefix}-knowledge"]
      ResourceType = "collection"
    }]
    AllowFromPublic = var.allow_public_access
    SourceVPCEs     = var.allow_public_access ? null : [aws_opensearchserverless_vpc_endpoint.knowledge[0].id]
  }])
}

resource "aws_opensearchserverless_vpc_endpoint" "knowledge" {
  count = var.allow_public_access ? 0 : 1

  name       = "${var.name_prefix}-knowledge-vpce"
  vpc_id     = var.vpc_id
  subnet_ids = var.subnet_ids

  security_group_ids = var.security_group_ids

  # Caught at plan time rather than as an opaque API error partway through an apply.
  lifecycle {
    precondition {
      condition     = var.vpc_id != null && length(var.subnet_ids) > 0
      error_message = "vpc_id and subnet_ids are required when allow_public_access is false. Either supply them or set allow_public_access = true for a sandbox."
    }
  }
}

# Data access is separate from network reachability in OpenSearch Serverless, and separate
# again from IAM: reaching the collection does not grant reading it, and neither does
# aoss:APIAccessAll on its own. Name the roles that actually issue queries — the retrieval
# tool's role, not the orchestrator's, which only invokes that Lambda and never touches
# the collection.
resource "aws_opensearchserverless_access_policy" "knowledge" {
  name = "${var.name_prefix}-knowledge-access"
  type = "data"

  policy = jsonencode([{
    Rules = [
      {
        ResourceType = "index"
        Resource     = ["index/${var.name_prefix}-knowledge/*"]
        Permission = [
          "aoss:ReadDocument",
          "aoss:WriteDocument",
          "aoss:CreateIndex",
          "aoss:UpdateIndex",
          "aoss:DescribeIndex",
        ]
      },
      {
        ResourceType = "collection"
        Resource     = ["collection/${var.name_prefix}-knowledge"]
        Permission   = ["aoss:DescribeCollection"]
      },
    ]
    Principal = var.access_principal_arns
  }])
}
