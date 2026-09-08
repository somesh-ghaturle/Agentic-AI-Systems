# Staging environment.
#
# Structurally identical to dev and prod — same modules, same wiring, same approval gate.
# Only the variables differ, which is the same rule the other two environments follow.
#
# What staging is FOR, since "between dev and prod" does not say much on its own: the
# dev/prod difference in this repository is not scale, it is posture. Dev runs with a
# public knowledge collection, execution payloads in logs, and no point-in-time recovery.
# Those are exactly the settings whose first real exercise would otherwise be the first
# prod apply — and a VPC-only collection that nobody can reach is the classic way for that
# apply to fail. Staging turns them all on, so the failure happens here instead.
#
# The rule for what staging takes from where:
#
#   From prod — every REVERSIBLE control
#     Knowledge collection    VPC-only, never public
#     Execution data in logs  OFF
#     Execution state         PITR on
#     Alarm topics            required
#     Trace emitter           required
#     Step budgets            prod's, not dev's
#
#   From dev — everything IRREVERSIBLE or merely expensive
#     Object Lock             never, hard-coded null
#     KMS deletion window     7 days
#     Retention               30 days, approval records 90
#     Archive lifecycle       expires at 90 days
#
# The split is the whole design. A staging environment that inherits prod's irreversible
# settings cannot be torn down and rebuilt, and one that is not rebuilt regularly stops
# resembling anything. Object Lock in particular must be decided before the bucket is
# created and can never be shortened afterwards, so it is not a variable here — it is a
# constant, and the constant is off.
#
# See the note in envs/dev/main.tf about deterministic ARNs breaking the module cycle;
# the same technique applies here for the same reason.

terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.58"
    }
  }

  # Remote state with locking. Staging is shared by definition — it is where more than one
  # person verifies a release — so local state is not viable here for the same reason it is
  # not viable in prod.
  #
  # backend "s3" {
  #   bucket         = "<your-tf-state-bucket>"
  #   key            = "agentic/staging/terraform.tfstate"
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
  name_prefix = "${var.project}-staging"

  # Cycle-breakers — see the note at the top of envs/dev/main.tf.
  state_machine_arn     = "arn:aws:states:${var.region}:${data.aws_caller_identity.current.account_id}:stateMachine:${local.name_prefix}-orchestrator"
  approval_executor_arn = "arn:aws:lambda:${var.region}:${data.aws_caller_identity.current.account_id}:function:${local.name_prefix}-approval-executor"

  tags = {
    Project     = var.project
    Environment = "staging"
    ManagedBy   = "terraform"
    Component   = "agentic-system"
    DataClass   = var.data_classification
  }
}

module "security" {
  source = "../../modules/security"

  name_prefix = local.name_prefix

  # Dev's window, not prod's. Staging gets torn down and rebuilt on purpose, and a 30-day
  # window leaves a scheduled-for-deletion key behind every time.
  key_deletion_window_days = 7

  create_guardrail = var.create_guardrail
  pii_entities     = var.pii_entities

  tags = local.tags
}

module "state" {
  source = "../../modules/state"

  name_prefix = local.name_prefix
  kms_key_arn = module.security.kms_key_arn

  # On, as in prod. PITR changes the table's billing and backup behavior, so leaving it
  # off here would mean prod runs a configuration staging never exercised.
  point_in_time_recovery = true

  tags = local.tags
}

module "archive" {
  source = "../../modules/archive"

  name_prefix = local.name_prefix
  kms_key_arn = module.security.kms_key_arn

  # Dev's lifecycle. Staging traces are not evidence — they are the output of a release
  # rehearsal, and keeping them past the next release costs money to store data nobody
  # will read.
  transition_ia_days      = 7
  transition_glacier_days = 30
  expiration_days         = var.archive_expiration_days

  # Never in staging, and deliberately not a variable. Object Lock cannot be enabled on an
  # existing bucket and COMPLIANCE mode cannot be shortened by anyone once set, so one
  # `terraform.tfvars` edit here would permanently strand the bucket of an environment
  # whose whole value is being disposable. Prod exposes this as a variable; staging does
  # not get the option.
  object_lock_retention_days = null

  tags = local.tags
}

module "networking" {
  source = "../../modules/networking"

  name_prefix = local.name_prefix

  # The same VPC the knowledge collection's endpoint lands in. One network, or the handler
  # ENIs and the collection endpoint are in two places that cannot reach each other.
  vpc_id     = var.vpc_id
  subnet_ids = var.subnet_ids

  tags = local.tags
}

module "knowledge" {
  source = "../../modules/knowledge"

  name_prefix = local.name_prefix
  kms_key_arn = module.security.kms_key_arn

  # VPC-only, exactly as in prod, and the single most valuable thing staging verifies.
  # A collection that is unreachable from where the retrieve tool actually runs fails at
  # query time rather than at apply, so the only way to find out is to run it.
  allow_public_access = false
  vpc_id              = var.vpc_id
  subnet_ids          = var.subnet_ids
  security_group_ids  = [module.networking.endpoint_security_group_id]

  # The retrieve tool's role, not the orchestrator's. Data access in OpenSearch Serverless
  # is a separate grant from IAM and from network reachability, and it names the principal
  # that actually issues the query — which is the tool Lambda. The orchestrator only
  # invokes that Lambda; it never touches the collection, so granting it here authorizes
  # nobody and every retrieval comes back 403.
  access_principal_arns = [module.tools.tool_role_arns_by_name["retrieve"]]

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

  # Required here as in prod. Without it the loop-bound and cost filters watch a log group
  # the state machine cannot write to and sit at zero, which reads as healthy — and a
  # staging environment that reports healthy for the wrong reason is worse than none.
  trace_emitter = var.trace_emitter

  alarm_topic_arns = var.alarm_topic_arns

  tags = local.tags
  # On the VPC, so the collection's endpoint is reachable at all. The security group
  # permits 443 to the interface endpoints and nothing else — there is no NAT here.
  subnet_ids         = var.subnet_ids
  security_group_ids = [module.networking.handler_security_group_id]

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
  # On the VPC, so the collection's endpoint is reachable at all. The security group
  # permits 443 to the interface endpoints and nothing else — there is no NAT here.
  subnet_ids         = var.subnet_ids
  security_group_ids = [module.networking.handler_security_group_id]

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

  # Longer than ordinary logs here too, though nothing like prod's seven years. Staging
  # approval records are how you reconstruct a rehearsal that went wrong, not evidence.
  log_retention_days = var.approval_log_retention_days

  tags = local.tags
  # On the VPC, so the collection's endpoint is reachable at all. The security group
  # permits 443 to the interface endpoints and nothing else — there is no NAT here.
  subnet_ids         = var.subnet_ids
  security_group_ids = [module.networking.handler_security_group_id]

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

  # OFF, as in prod. Staging is where a production-shaped corpus and production-shaped
  # payloads get exercised, and turning this on is how a payload nobody meant to keep ends
  # up in CloudWatch. If dev's behaviour is what you want, use dev.
  log_execution_data = false
  log_retention_days = var.log_retention_days

  tags = local.tags
}
