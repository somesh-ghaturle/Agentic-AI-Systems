# Dev environment.
#
# Deliberately cheaper and more permissive than prod, with the differences confined to
# variables rather than to structure. The wiring here is identical to prod — that is the
# point. An approval gate you only exercise in prod is an approval gate you have not
# tested.
#
# What differs in dev: shorter retention, no PITR, a public knowledge collection, a lower
# cost alarm, and log_execution_data on (dev payloads should be synthetic).
#
# ---------------------------------------------------------------------------
# A note on the module wiring, because it looks indirect on purpose
#
# The enforcement flow is inherently circular: the orchestrator invokes the validator,
# the executor invokes write tools, and the executor resolves the orchestrator's task
# token. Wired literally, that is a Terraform dependency cycle:
#
#     orchestration -> approval -> orchestration
#
# It is broken by constructing the state machine ARN from known values rather than
# reading it back off the resource. The name is deterministic, so the ARN is too. This is
# the standard resolution and it keeps every real permission boundary intact.
# ---------------------------------------------------------------------------

terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Remote state with locking. Uncomment and fill in before the first apply — local state
  # for shared infrastructure means two people applying at once corrupt each other's work.
  #
  # backend "s3" {
  #   bucket         = "<your-tf-state-bucket>"
  #   key            = "agentic/dev/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "<your-tf-lock-table>"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = local.tags
  }
}

data "aws_caller_identity" "current" {}

locals {
  name_prefix = "${var.project}-dev"

  # Cycle-breakers: the same ARNs the resources will produce, known before they exist
  # because the names are deterministic. See the note at the top of this file.
  state_machine_arn     = "arn:aws:states:${var.region}:${data.aws_caller_identity.current.account_id}:stateMachine:${local.name_prefix}-orchestrator"
  approval_executor_arn = "arn:aws:lambda:${var.region}:${data.aws_caller_identity.current.account_id}:function:${local.name_prefix}-approval-executor"

  tags = {
    Project     = var.project
    Environment = "dev"
    ManagedBy   = "terraform"
    Component   = "agentic-system"
  }
}

module "security" {
  source = "../../modules/security"

  name_prefix = local.name_prefix

  # Shorter window so a torn-down dev environment does not leave a key lingering.
  key_deletion_window_days = 7

  # Off by default here; turn on when the model layer runs on Bedrock.
  create_guardrail = false

  tags = local.tags
}

module "state" {
  source = "../../modules/state"

  name_prefix            = local.name_prefix
  kms_key_arn            = module.security.kms_key_arn
  point_in_time_recovery = false

  tags = local.tags
}

module "archive" {
  source = "../../modules/archive"

  name_prefix = local.name_prefix
  kms_key_arn = module.security.kms_key_arn

  # Dev traces are not evidence. Expire them.
  transition_ia_days      = 7
  transition_glacier_days = 30
  expiration_days         = 90

  tags = local.tags
}

module "knowledge" {
  source = "../../modules/knowledge"

  name_prefix = local.name_prefix
  kms_key_arn = module.security.kms_key_arn

  # Acceptable ONLY because dev holds synthetic documents. If you load a production
  # corpus into dev, this must become false and the VPC inputs must be supplied.
  allow_public_access = true

  access_principal_arns = [module.orchestration.role_arn]

  tags = local.tags
}

module "observability" {
  source = "../../modules/observability"

  name_prefix        = local.name_prefix
  kms_key_arn        = module.security.kms_key_arn
  log_retention_days = 14

  state_machine_arn = local.state_machine_arn

  # Low on purpose. In dev this is a runaway-loop detector, not a budget.
  daily_cost_threshold_usd = 25

  alarm_topic_arns = var.alarm_topic_arns

  tags = local.tags
}

# The tool layer. Read tools are invoked by the orchestrator; write tools only by the
# approval executor. That split is enforced in the module, not by convention here.
module "tools" {
  source = "../../modules/tools"

  name_prefix = local.name_prefix
  kms_key_arn = module.security.kms_key_arn
  tools       = var.tools

  orchestrator_state_machine_arn = local.state_machine_arn
  approval_executor_arn          = local.approval_executor_arn

  # Traces go to the shared group the metric filters watch, not to each function's own
  # log group. Handlers read TRACE_LOG_GROUP; the ARN grants them the write.
  trace_log_group_name = module.observability.trace_log_group_name
  trace_log_group_arn  = module.observability.trace_log_group_arn

  # The retrieval handler resolves the collection endpoint from this name at cold start.
  # Passing the endpoint itself would mean tools -> knowledge -> orchestration -> tools.
  common_environment = {
    KNOWLEDGE_COLLECTION = "${local.name_prefix}-knowledge"
  }

  log_retention_days = 14

  tags = local.tags
}

module "approval" {
  source = "../../modules/approval"

  name_prefix = local.name_prefix
  kms_key_arn = module.security.kms_key_arn

  validator = var.approval_validator
  executor  = var.approval_executor

  write_tool_arns                = module.tools.write_tool_arns
  orchestrator_state_machine_arn = local.state_machine_arn

  trace_log_group_name = module.observability.trace_log_group_name
  trace_log_group_arn  = module.observability.trace_log_group_arn

  log_retention_days = 30

  tags = local.tags
}

module "orchestration" {
  source = "../../modules/orchestration"

  name_prefix = local.name_prefix
  definition  = file("${path.module}/state-machine.json")
  kms_key_arn = module.security.kms_key_arn

  state_table_arn    = module.state.table_arn
  archive_bucket_arn = module.archive.bucket_arn
  approval_topic_arn = module.approval.approval_topic_arn

  tool_function_arns = concat(
    module.tools.read_tool_arns,
    [module.approval.validator_arn],
  )

  # Safe in dev where payloads are synthetic. Revisit before any real data lands here.
  log_execution_data = true
  log_retention_days = 14

  tags = local.tags
}
