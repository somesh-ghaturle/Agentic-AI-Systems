output "bucket_id" {
  description = "Trace archive bucket name, for the orchestrator's environment."
  value       = aws_s3_bucket.archive.id
}

output "bucket_arn" {
  description = "Trace archive bucket ARN, for least-privilege IAM policies."
  value       = aws_s3_bucket.archive.arn
}
