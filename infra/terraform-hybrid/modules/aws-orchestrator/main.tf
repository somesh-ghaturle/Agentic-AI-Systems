resource "aws_iam_role" "orchestrator" {
  count = var.enable_resources ? 1 : 0

  name = "${var.name_prefix}-hybrid-orchestrator"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "states.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_sfn_state_machine" "orchestrator" {
  count = var.enable_resources ? 1 : 0

  name       = "${var.name_prefix}-hybrid"
  role_arn   = aws_iam_role.orchestrator[0].arn
  definition = var.definition
  tags = {
    Component = "hybrid-orchestrator"
    Managed   = "terraform"
  }
}
