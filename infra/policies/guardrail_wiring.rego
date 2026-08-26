# A guardrail that is declared but not attached filters nothing.
#
# This is the failure mode the modules themselves name. terraform-azure's model-integration
# module says it outright above the policy resource: "Unattached, it exists and does nothing,
# which is the failure mode worth watching for: the policy shows up in the portal, looks like
# a control, and filters nothing." terraform-gcp says the same about the floor setting in
# outputs.tf — without it "a handler that omits the sanitize call reaches the model unfiltered
# and nothing reports it."
#
# Neither checkov nor the write-boundary suites cover this. checkov asks whether a resource is
# configured safely, not whether anything points at it; infra/*/tests/ assert the write
# boundary, which is a different control. The gap is specifically "declared but not wired",
# and it is invisible in a plan diff because adding the guardrail and forgetting the reference
# both show up as resources created.
#
# Each tree wires its guardrail with a different primitive, which is deliberate — see
# docs/DECISION-LOGS/0002-azure-openai-vs-claude.md. The invariant is shared even though the
# mechanism is not, so it is one policy with four rules rather than four copied files.

package main

import rego.v1

# AWS — the guardrail is applied through a version. Without one, the application has nothing
# to pin to and the guardrail is a draft nothing evaluates.
deny contains msg if {
	some name in resource_names("aws_bedrock_guardrail")
	not references(attr_strings("aws_bedrock_guardrail_version", "guardrail_arn"), sprintf("aws_bedrock_guardrail.%s", [name]))

	msg := sprintf(
		"aws_bedrock_guardrail.%s has no aws_bedrock_guardrail_version referencing it — the guardrail exists as a draft and no application can pin to it.",
		[name],
	)
}

# Azure — naming the policy on the deployment is the line that makes it apply.
deny contains msg if {
	some name in resource_names("azurerm_cognitive_account_rai_policy")
	not references(attr_strings("azurerm_cognitive_deployment", "rai_policy_name"), sprintf("azurerm_cognitive_account_rai_policy.%s", [name]))

	msg := sprintf(
		"azurerm_cognitive_account_rai_policy.%s is not named by any azurerm_cognitive_deployment.rai_policy_name — it will show up in the portal and filter nothing.",
		[name],
	)
}

# GCP — the template describes filters; the floor setting is what makes Vertex apply them to
# every generateContent in the project. Template alone leaves enforcement opt-in per handler.
deny contains msg if {
	count(resource_names("google_model_armor_template")) > 0
	count(resource_names("google_model_armor_floorsetting")) == 0

	msg := "google_model_armor_template is declared with no google_model_armor_floorsetting — filtering becomes opt-in per handler, and a handler that omits the sanitize call reaches the model unfiltered."
}

# Snowflake — the guard is an option on COMPLETE, not an object, so there is nothing to
# attach and nothing to name. What makes it apply is that the only Cortex-capable role in
# the tree is the one nothing logs in as, and every caller reaches the model through the
# wrapper instead.
#
# Two ways that fails, both valid config:
#
#   1. The wrapper exists and is granted to nobody. Callers cannot use it, so they use raw
#      COMPLETE — the wrapper sits in the schema looking like a control and filters nothing.
#   2. CORTEX_USER is granted directly to a caller role. The wrapper still exists, still
#      works, and is now optional.
#
# Rule 1 is the direct analogue of the three above: declared but not wired.
#
# Note what it matches on. The obvious check — look for the literal "COMPLETE_GUARDED" in a
# grant's object_name — reports a false positive on correct config, because the grant names
# the procedure through `local.complete_signature` and the parser preserves that
# interpolation verbatim. The literal name never appears. Matching the local's name is what
# actually tracks the wiring, for the same reason the header gives: nothing here evaluates
# HCL, so a reference is whatever text the expression contains.
deny contains msg if {
	some name in resource_names("snowflake_procedure_sql")
	name == "complete_guarded"
	not references(nested_attr_strings("snowflake_grant_privileges_to_account_role", "on_schema_object", "object_name"), "complete_signature")

	msg := "snowflake_procedure_sql.complete_guarded is granted to no role — callers cannot reach it and will call SNOWFLAKE.CORTEX.COMPLETE unguarded instead."
}

# Rule 2 is the bypass. The tool owner is the one role that legitimately holds CORTEX_USER,
# because it owns the wrapper and the wrapper runs as owner.
deny contains msg if {
	some i
	some _, blocks in object.get(input[i], ["contents", "resource", "snowflake_grant_database_role"], {})
	some block in blocks
	contains(block.database_role_name, "CORTEX_USER")
	block.parent_role_name != "${var.tool_owner_role}"

	msg := sprintf(
		"SNOWFLAKE.CORTEX_USER is granted to %s rather than to the tool owner — that role can call COMPLETE with no guardrail, and the wrapper becomes optional.",
		[block.parent_role_name],
	)
}
