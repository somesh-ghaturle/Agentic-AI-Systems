# Production environment.
#
# Structurally identical to dev — same modules, same wiring, same approval gate. Only the
# variables differ. That sameness is deliberate: a gate exercised only in prod is a gate
# nobody has tested.
#
# What is hardened here relative to dev:
#
#   Knowledge collection    VPC-only, never public
#   Execution state         PITR on
#   Trace archive           no expiry by default; Object Lock available
#   Execution data in logs  OFF — payloads carry customer data
#   Retention               365 days, approval records longer
#   KMS deletion window     30 days, the maximum
#
# See the note in envs/dev/main.tf about deterministic ARNs breaking the module cycle;
# the same technique applies here for the same reason.

terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Remote state is not optional in prod. Uncomment and fill in before the first apply.
  #
  # backend "s3" {
  #   bucket         = "<your-tf-state-bucket>"
  #   key            = "agentic/prod/terraform.tfstate"
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
  name_prefix = "${var.project}-prod"

  # Cycle-breakers — see the note at the top of envs/dev/main.tf.
  state_machine_arn     = "arn:aws:states:${var.region}:${data.aws_caller_identity.current.account_id}:stateMachine:${local.name_prefix}-orchestrator"
  approval_executor_arn = "arn:aws:lambda:${var.region}:${data.aws_caller_identity.current.account_id}:function:${local.name_prefix}-approval-executor"

  tags = {
    Project     = var.project
    Environment = "prod"
    ManagedBy   = "terraform"
    Component   = "agentic-system"
    DataClass   = var.data_classification
  }
}

module "security" {
  source = "../../modules/security"

  name_prefix = local.name_prefix

  # Maximum window. A key deleted in error takes its data with it.
  key_deletion_window_days = 30

  create_guardrail = var.create_guardrail
  pii_entities     = var.pii_entities

  tags = local.tags
}

module "state" {
  source = "../../modules/state"

  name_prefix = local.name_prefix
  kms_key_arn = module.security.kms_key_arn

  # Resuming recovers lost state; nothing recovers corrupted state but this.
  point_in_time_recovery = true

  tags = local.tags
}

module "archive" {
  source = "../../modules/archive"

  name_prefix = local.name_prefix
  kms_key_arn = module.security.kms_key_arn

  transition_ia_days      = 30
  transition_glacier_days = 90

  # Null retains indefinitely. Set this from your records policy — it is a compliance
  # decision, not an infrastructure default.
  expiration_days = var.archive_expiration_days

  # Set only in an audit context, and only deliberately: COMPLIANCE mode cannot be
  # shortened by anyone, and it must be decided before the bucket is created.
  object_lock_retention_days = var.archive_object_lock_days

  tags = local.tags
}

module "knowledge" {
  source = "../../modules/knowledge"

  name_prefix = local.name_prefix
  kms_key_arn = module.security.kms_key_arn

  # Never public in prod. The corpus may hold customer documents, and metadata filtering
  # at query time is what prevents cross-tenant leakage — but reachability comes first.
  allow_public_access = false
  vpc_id              = var.vpc_id
  subnet_ids          = var.subnet_ids
  security_group_ids  = var.security_group_ids

  access_principal_arns = [module.orchestration.role_arn]

  tags = local.tags
}

module "observability" {
  source = "../../modules/observability"

  name_prefix        = local.name_prefix
  kms_key_arn        = module.security.kms_key_arn
  log_retention_days = var.log_retention_days

  state_machine_arn = local.state_machine_arn

  daily_cost_threshold_usd = var.daily_cost_threshold_usd
  schema_failure_threshold = 5

  # The orchestrator's own records — terminal outcomes, the loop bound firing — reach the
  # trace log group through this function. Required in prod: without it the loop-bound and
  # cost filters watch a group the state machine cannot write to and sit at zero, which
  # reads as healthy.
  trace_emitter = var.trace_emitter

  alarm_topic_arns = var.alarm_topic_arns

  tags = local.tags
}

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

  log_retention_days = var.log_retention_days

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

  # Approval records are audit evidence and outlive ordinary logs.
  log_retention_days = var.approval_log_retention_days

  tags = local.tags
}

module "orchestration" {
  source = "../../modules/orchestration"

  name_prefix = local.name_prefix
  kms_key_arn = module.security.kms_key_arn

  # Templated rather than read verbatim. The definition names four ARNs that only exist
  # after apply; passing the file as-is shipped the literal placeholders straight into the
  # state machine, where they fail at runtime rather than at plan.
  definition = templatefile("${path.module}/state-machine.json.tftpl", {
    retrieve_tool_arn  = module.tools.tool_arns_by_name["retrieve"]
    validator_arn      = module.approval.validator_arn
    approval_topic_arn = module.approval.approval_topic_arn
    trace_emitter_arn  = module.observability.trace_emitter_arn

    # The model step is yours to write; the reference ships no handler for it. Declare a
    # tool named "reason" in terraform.tfvars and it wires itself.
    reason_tool_arn = try(module.tools.tool_arns_by_name["reason"], "REASON_TOOL_NOT_CONFIGURED")
  })

  state_table_arn    = module.state.table_arn
  archive_bucket_arn = module.archive.bucket_arn
  approval_topic_arn = module.approval.approval_topic_arn

  tool_function_arns = concat(
    module.tools.read_tool_arns,
    [module.approval.validator_arn],
    module.observability.trace_emitter_arn == null ? [] : [module.observability.trace_emitter_arn],
  )

  # OFF in prod. State input/output carries customer data, and CloudWatch is not where
  # you want an unmasked payload to land. Turn on only for a scoped investigation, with
  # the privacy implications understood.
  log_execution_data = false
  log_retention_days = var.log_retention_days

  tags = local.tags
}
