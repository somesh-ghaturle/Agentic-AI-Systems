# Long-term archive — BUILDING-BLOCKS.md §3
#
# Full traces, prompt versions, model versions, tool calls with arguments and results,
# token counts, costs, latency, outcomes. Write-once, read rarely, retained long.
#
# The doc calls this "the thing teams most regret not having from day one." It is cheap
# to turn on now and impossible to reconstruct later.
#
# PII MASKING IS AN APPLICATION RESPONSIBILITY. Terraform cannot enforce it. Mask before
# the write, not after — PRODUCTION-PRINCIPLES.md "Mask PII before it reaches the model".

terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

resource "aws_s3_bucket" "archive" {
  bucket = "${var.name_prefix}-trace-archive"

  # Must be set at creation — S3 cannot enable Object Lock on an existing bucket, so
  # turning this on later means recreating the bucket and migrating objects. Decide
  # before the first apply if you are in an audit context.
  object_lock_enabled = var.object_lock_retention_days != null

  tags = merge(var.tags, {
    Component = "trace-archive"
    Layer     = "memory-and-state"
  })
}

# Traces are audit evidence. Versioning means an overwrite does not destroy the record.
resource "aws_s3_bucket_versioning" "archive" {
  bucket = aws_s3_bucket.archive.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "archive" {
  bucket = aws_s3_bucket.archive.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.kms_key_arn == null ? "AES256" : "aws:kms"
      kms_master_key_id = var.kms_key_arn
    }
    bucket_key_enabled = var.kms_key_arn != null
  }
}

resource "aws_s3_bucket_public_access_block" "archive" {
  bucket = aws_s3_bucket.archive.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Read-rarely data does not belong in Standard forever. These transitions cut the cost of
# retention enough that "keep everything" stays affordable, which is the point.
resource "aws_s3_bucket_lifecycle_configuration" "archive" {
  bucket = aws_s3_bucket.archive.id

  rule {
    id     = "tier-and-expire"
    status = "Enabled"

    filter {}

    transition {
      days          = var.transition_ia_days
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = var.transition_glacier_days
      storage_class = "GLACIER"
    }

    # Retention is a compliance decision, not a default. See ENTERPRISE-ADAPTATION.md —
    # in a regulated environment this number comes from your records policy.
    dynamic "expiration" {
      for_each = var.expiration_days == null ? [] : [var.expiration_days]
      content {
        days = expiration.value
      }
    }

    noncurrent_version_expiration {
      noncurrent_days = var.noncurrent_version_expiration_days
    }
  }
}

# Object Lock equivalent for audit contexts: prevents deletion of trace evidence within
# the retention window, including by an administrator. Off by default because it is
# irreversible once set and genuinely inconvenient if enabled without intent.
resource "aws_s3_bucket_object_lock_configuration" "archive" {
  count = var.object_lock_retention_days == null ? 0 : 1

  bucket = aws_s3_bucket.archive.id

  rule {
    default_retention {
      mode = "COMPLIANCE"
      days = var.object_lock_retention_days
    }
  }
}
