# Execution state — BUILDING-BLOCKS.md section 3
#
# The working memory of an in-flight request: current step, accumulated parameters,
# tool results, approval status, retry counts, correlation ID.
#
# Two properties the architecture doc treats as non-negotiable, both implemented here:
#   - Survives process restarts (state lives outside the process, keyed by correlation ID)
#   - Explicit and serializable (inspectable and resumable after the fact)

terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

resource "aws_dynamodb_table" "execution_state" {
  name = "${var.name_prefix}-execution-state"

  # Read/write on every step with unpredictable per-request volume. On-demand avoids
  # capacity planning for a workload whose shape you do not know yet; switch to
  # PROVISIONED once traffic is understood and steady.
  billing_mode = var.billing_mode
  hash_key     = "correlation_id"

  # The correlation ID is the single key tying execution state to traces and to the
  # archive. One ID from request to response — BUILDING-BLOCKS.md section 4 "Non-negotiables".
  attribute {
    name = "correlation_id"
    type = "S"
  }

  # Workflow state is short-lived by design. TTL reclaims it automatically rather than
  # accumulating rows nobody reads. The archive holds anything with lasting value.
  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  # Recovery for the case where a bad deploy corrupts in-flight state rather than
  # losing it. Losing state is recoverable by resuming; corrupting it is not.
  point_in_time_recovery {
    enabled = var.point_in_time_recovery
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = var.kms_key_arn
  }

  tags = merge(var.tags, {
    Component = "execution-state"
    Layer     = "memory-and-state"
  })
}
