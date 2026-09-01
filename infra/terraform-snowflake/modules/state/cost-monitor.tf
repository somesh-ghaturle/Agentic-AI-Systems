# Cost monitoring — the one place this tree's warehouse spend is bounded rather than merely
# observed.
#
# The other three trees alarm on cost_usd, summed from application trace records — a proxy for
# LLM API spend that says nothing about the cloud's own bill. That signal does not exist here in
# the same shape: this warehouse's spend is credit-seconds Snowflake bills directly, not a field
# an agent chooses to emit. A resource monitor reads it from the platform itself.
#
# It is also a materially different kind of control. The other three trees' alarms only ever
# notify — nothing on AWS, Azure, or GCP stops a runaway loop from spending money, it just tells
# someone it happened. `suspend_trigger` and `suspend_immediate_trigger` below can actually stop
# it, which is why they default to null: an enforcement action that isn't there on the other
# three trees is not something to turn on silently by adding this file.

resource "snowflake_resource_monitor" "warehouse_cost" {
  count = var.cost_monitor_credit_quota == null ? 0 : 1

  name         = "${var.name_prefix}_COST_MONITOR"
  credit_quota = var.cost_monitor_credit_quota
  frequency    = var.cost_monitor_frequency

  # The provider requires start_timestamp whenever frequency is set. IMMEDIATELY resolves to
  # today at apply time rather than a date fixed in this file — the provider's own docs note
  # that show_output can then read as drift between runs; that is a read-back cosmetic, not a
  # plan that wants to change anything, so it is accepted rather than pinning a literal date.
  start_timestamp = "IMMEDIATELY"

  notify_triggers = var.cost_monitor_notify_triggers
  notify_users    = var.cost_monitor_notify_users

  # Both null by default. A resource monitor with only notify_triggers set is alert-only,
  # same posture as the other three trees' cost alarms — see the variables' own descriptions
  # for why suspension defaults on in dev/staging and off in prod.
  suspend_trigger           = var.cost_monitor_suspend_trigger
  suspend_immediate_trigger = var.cost_monitor_suspend_immediate_trigger
}
