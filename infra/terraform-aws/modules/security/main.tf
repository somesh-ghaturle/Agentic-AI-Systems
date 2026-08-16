# Security — PRODUCTION-PRINCIPLES.md, AGENT-SECURITY.md
#
# The framing that matters, from AGENT-SECURITY.md: instructions and data share a channel,
# so content filtering is a mitigation and capability limits are the control. A guardrail
# that catches most injection attempts is worth having. A write path the model cannot
# reach without human approval is worth more.
#
# That is why the real security work in this stack lives in modules/tools (read/write
# split) and modules/approval (the gate), not here. This module supplies the key material
# and the model-layer filter that sit underneath them.

terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.58"
    }
  }
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# ---------------------------------------------------------------------------
# Customer-managed key
#
# Used across execution state, the trace archive, the knowledge collection, and logs.
# One key with a readable policy beats per-service AWS-owned keys when an auditor asks
# who can read what.
# ---------------------------------------------------------------------------

resource "aws_kms_key" "main" {
  description             = "Agentic system data at rest — ${var.name_prefix}"
  deletion_window_in_days = var.key_deletion_window_days
  enable_key_rotation     = true

  policy = data.aws_iam_policy_document.key.json

  tags = merge(var.tags, {
    Component = "kms"
    Layer     = "security"
  })
}

resource "aws_kms_alias" "main" {
  name          = "alias/${var.name_prefix}-agentic"
  target_key_id = aws_kms_key.main.key_id
}

data "aws_iam_policy_document" "key" {
  # Without this the key becomes unmanageable — AWS requires the account root to retain
  # administrative access or the key can be orphaned.
  statement {
    sid    = "EnableAccountAdmin"
    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
    actions   = ["kms:*"]
    resources = ["*"]
  }

  # AWS services encrypting on the system's behalf.
  #
  # sns.amazonaws.com is load-bearing rather than routine: the approval topics are
  # encrypted with this key, and SNS needs its own grant to decrypt a message for
  # delivery. Without it the publish succeeds and the notification never arrives, which
  # is the failure mode where an approval request silently reaches nobody and the
  # execution sits blocked until it times out.
  #
  # Lambda is deliberately absent. Environment-variable decryption runs under each
  # function's execution role, so those grants live with the roles, not here.
  statement {
    sid    = "AllowServiceUse"
    effect = "Allow"
    principals {
      type = "Service"
      identifiers = [
        "logs.${data.aws_region.current.name}.amazonaws.com",
        "s3.amazonaws.com",
        "dynamodb.amazonaws.com",
        "sns.amazonaws.com",
      ]
    }
    actions = [
      "kms:Encrypt",
      "kms:Decrypt",
      "kms:ReEncrypt*",
      "kms:GenerateDataKey*",
      "kms:DescribeKey",
    ]
    resources = ["*"]
  }
}

# ---------------------------------------------------------------------------
# Bedrock guardrail — a mitigation layer, not the control
#
# Worth having: it catches a meaningful share of injection attempts and PII leakage
# cheaply. Worth being honest about: a determined injection will get past it, which is
# exactly why the write path is gated separately.
# ---------------------------------------------------------------------------

resource "aws_bedrock_guardrail" "main" {
  count = var.create_guardrail ? 1 : 0

  name                      = "${var.name_prefix}-guardrail"
  blocked_input_messaging   = var.blocked_input_message
  blocked_outputs_messaging = var.blocked_output_message
  kms_key_arn               = aws_kms_key.main.arn

  content_policy_config {
    dynamic "filters_config" {
      for_each = var.content_filters
      content {
        type            = filters_config.value.type
        input_strength  = filters_config.value.input_strength
        output_strength = filters_config.value.output_strength
      }
    }
  }

  # PII masking at the model boundary. PRODUCTION-PRINCIPLES.md is specific that masking
  # happens before data reaches the model — this is a backstop for what upstream masking
  # misses, not a replacement for it.
  dynamic "sensitive_information_policy_config" {
    for_each = length(var.pii_entities) > 0 ? [1] : []
    content {
      dynamic "pii_entities_config" {
        for_each = var.pii_entities
        content {
          type   = pii_entities_config.value.type
          action = pii_entities_config.value.action
        }
      }
    }
  }

  tags = merge(var.tags, {
    Component = "guardrail"
    Layer     = "security"
  })
}

resource "aws_bedrock_guardrail_version" "main" {
  count = var.create_guardrail ? 1 : 0

  guardrail_arn = aws_bedrock_guardrail.main[0].guardrail_arn
  description   = "Managed by Terraform"

  # Pin the application to a version rather than DRAFT: a guardrail edit should not change
  # production behavior until someone deploys it deliberately.
  lifecycle {
    create_before_destroy = true
  }
}
