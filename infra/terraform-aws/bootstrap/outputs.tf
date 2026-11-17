output "state_bucket" {
  description = "Bucket name for the `bucket` argument of each environment's backend block."
  value       = aws_s3_bucket.state.id
}

output "backend_block" {
  description = "The backend block to paste into an environment root, with `<env>` replaced."
  value       = <<-EOT
    backend "s3" {
      bucket       = "${aws_s3_bucket.state.id}"
      key          = "agentic/<env>/terraform.tfstate"
      region       = "${var.region}"
      use_lockfile = true
      encrypt      = true
    }
  EOT
}
