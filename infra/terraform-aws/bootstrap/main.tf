# Remote state bootstrap — the bucket the environment roots keep their state in.
#
# Every root under envs/ applies against a local state file until its `backend "s3"` block
# is uncommented, and that block needs a bucket to point at. This root creates it. It is
# applied once per account, before any environment, and it is the one root whose own state
# stays local: a bucket cannot hold the state that records its own creation. Keep that
# local state file somewhere backed up, or re-import the bucket if it is lost — one
# resource, not the dozens an environment root would need.
#
# Nothing here is part of the agent. No module depends on it and the write boundary does
# not pass through it. It is a root of its own, not a module, so that an environment root
# can never destroy the bucket holding its own state.
#
# Locking uses the S3 backend's own lock file (`use_lockfile`), which needs Terraform 1.10
# or newer. The trees' floor is 1.6; on a version below 1.10 add a DynamoDB table with a
# `LockID` string hash key and name it in the backend block as `dynamodb_table`.

terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.58"
    }
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project   = var.project
      ManagedBy = "terraform"
      Component = "terraform-state"
    }
  }
}

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "state" {
  # Account ID in the name because bucket names are global: `<project>-tfstate` is taken
  # by whoever copied this tree first.
  bucket = "${var.project}-tfstate-${data.aws_caller_identity.current.account_id}"

  # State is the one thing in this account that cannot be rebuilt from the configuration.
  # Removing this line is the deliberate act a `destroy` should require.
  lifecycle {
    prevent_destroy = true
  }
}

# The recovery path. A corrupted or truncated state file is restored by reading back the
# previous version, which only exists if versioning was on before the bad write.
resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.state.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "state" {
  bucket = aws_s3_bucket.state.id

  rule {
    apply_server_side_encryption_by_default {
      # State can carry resource attributes that are sensitive. The AWS-managed key is
      # enough to keep it encrypted at rest without this root owning a key policy.
      sse_algorithm = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "state" {
  bucket = aws_s3_bucket.state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Old versions are the recovery path, not an archive. Keep a bounded window of them.
resource "aws_s3_bucket_lifecycle_configuration" "state" {
  bucket = aws_s3_bucket.state.id

  rule {
    id     = "expire-old-state-versions"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days = var.noncurrent_version_retention_days
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  depends_on = [aws_s3_bucket_versioning.state]
}

# State is read and written by Terraform over TLS and by nothing else.
data "aws_iam_policy_document" "tls_only" {
  statement {
    sid     = "DenyInsecureTransport"
    effect  = "Deny"
    actions = ["s3:*"]

    resources = [
      aws_s3_bucket.state.arn,
      "${aws_s3_bucket.state.arn}/*",
    ]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "state" {
  bucket = aws_s3_bucket.state.id
  policy = data.aws_iam_policy_document.tls_only.json

  depends_on = [aws_s3_bucket_public_access_block.state]
}
