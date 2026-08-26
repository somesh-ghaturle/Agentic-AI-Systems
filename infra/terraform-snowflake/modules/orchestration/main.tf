# Orchestration — the scheduled half, and an honest note about the rest
#
# The other three trees orchestrate with a service built for it: Step Functions on AWS,
# Durable Functions on Azure, Workflows on GCP. Each one holds a long-running execution,
# suspends it at an approval, and resumes when a token comes back. That suspend-and-resume
# primitive is what makes a human approval a *step* rather than a poll.
#
# Snowflake has no equivalent, and it is worth being direct about that rather than
# pretending a Task is one. A Task is a scheduler: it runs a statement on a cadence or
# after another Task. It cannot suspend awaiting an external event and it holds no
# per-execution continuation. So the approval flow in this tree is a poll, not a callback:
#
#   AWS/Azure/GCP   propose -> suspend execution -> human approves -> resume with token
#   Snowflake       propose -> record PENDING -> human approves -> a Task notices -> claim
#
# The write boundary is unaffected — it is a grant, and grants do not care how the
# executor was woken. What is affected is latency and cost: an approval is noticed on the
# next Task run rather than instantly, and the Task resumes a warehouse each time it looks.
# `schedule` is therefore a direct cost lever, and the default here is deliberately slow.
#
# The alternative is Snowpark Container Services, which does hold a long-running process
# and could implement a real callback. It needs a compute pool that bills whenever it is
# not suspended, which is a different cost shape than everything else in this tree. It is
# left out rather than half-built; see ARCHITECTURE.md, "Remaining work".

terraform {
  required_version = ">= 1.6"
  required_providers {
    snowflake = {
      source  = "snowflakedb/snowflake"
      version = "~> 2.20"
    }
  }
}

# ---------------------------------------------------------------------------
# The approval sweeper
#
# Finds APPROVED records nothing has claimed and claims them. This is the executor's
# wake-up, and it runs as a task owned by a role that holds the executor's grants.
#
# It deliberately does not call the write tool itself. The Task claims; the handler
# executes. Splitting them keeps the write invocation on a path that can log, retry and
# resolve, rather than inside a scheduler whose only failure signal is a task history row.
# ---------------------------------------------------------------------------

resource "snowflake_task" "approval_sweeper" {
  database  = var.database_name
  schema    = var.schema_name
  name      = "${var.name_prefix}_APPROVAL_SWEEPER"
  warehouse = var.warehouse_name

  schedule {
    minutes = var.sweep_interval_minutes
  }

  # Started false by default. A task that begins sweeping the moment it is created will
  # do so before the grants below have settled, and its first few runs fail in a way that
  # looks like a permissions bug. Start it deliberately, after an apply completes.
  started = var.task_started

  # Overlapping runs would let two sweeps claim in parallel. That is survivable — the
  # claim is atomic and one of them loses — but it doubles warehouse time to achieve
  # nothing.
  allow_overlapping_execution = false

  # A sweep that has not finished in this long is stuck, and letting it run is paying for
  # a hang. Comfortably under the approval module's stale-claim window so a killed sweep
  # is reclaimed rather than blocking.
  user_task_timeout_ms = var.task_timeout_ms

  suspend_task_after_num_failures = var.suspend_after_failures

  sql_statement = <<-SQL
    SELECT ${var.database_name}.${var.schema_name}.CLAIM_APPROVAL(APPROVAL_ID, ARGUMENTS_FINGERPRINT)
      FROM ${var.database_name}.${var.schema_name}.APPROVALS
     WHERE STATUS = 'APPROVED'
     LIMIT ${var.sweep_batch_size}
  SQL

  comment = "Claims approved proposals on a cadence. Snowflake has no suspend-and-resume primitive; see the module header."
}

# The task runs as its owner, so the owner needs what the executor has. Granting the
# executor role to the task owner rather than the reverse matters: the arrow points from
# the machinery to the capability, never from a caller role back up into it.
resource "snowflake_grant_account_role" "sweeper_role" {
  role_name        = var.executor_role
  parent_role_name = var.task_owner_role
}

resource "snowflake_grant_privileges_to_account_role" "task_execution" {
  account_role_name = var.task_owner_role
  privileges        = ["EXECUTE TASK"]
  on_account        = true
}
