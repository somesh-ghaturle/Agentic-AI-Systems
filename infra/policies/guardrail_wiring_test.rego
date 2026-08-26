# Unit tests for guardrail_wiring.rego, run by `conftest verify`.
#
# These exist because a policy that passes is indistinguishable from a policy that cannot
# fail. Each rule is tested twice: once against config that wires the guardrail correctly,
# where it must stay silent, and once against config missing exactly the wiring reference,
# where it must fire. Deleting a rule body would turn the second case green and is the
# failure these catch.
#
# `input` here is shaped the way `--combine` shapes it — an array of {path, contents} — so
# the tests exercise the same accessors the real run does.

package main

import rego.v1

combined(resources) := [{"path": "test.tf", "contents": {"resource": resources}}]

# --- AWS ------------------------------------------------------------------

test_aws_guardrail_without_version_is_denied if {
	result := deny with input as combined({"aws_bedrock_guardrail": {"main": [{"name": "g"}]}})
	count(result) == 1
}

test_aws_guardrail_with_version_is_allowed if {
	result := deny with input as combined({
		"aws_bedrock_guardrail": {"main": [{"name": "g"}]},
		"aws_bedrock_guardrail_version": {"main": [{"guardrail_arn": "${aws_bedrock_guardrail.main[0].guardrail_arn}"}]},
	})
	count(result) == 0
}

# A version pointing at a different guardrail must not satisfy the check.
test_aws_version_referencing_another_guardrail_is_denied if {
	result := deny with input as combined({
		"aws_bedrock_guardrail": {"main": [{"name": "g"}]},
		"aws_bedrock_guardrail_version": {"other": [{"guardrail_arn": "${aws_bedrock_guardrail.unrelated[0].guardrail_arn}"}]},
	})
	count(result) == 1
}

# --- Azure ----------------------------------------------------------------

test_azure_rai_policy_not_named_by_deployment_is_denied if {
	result := deny with input as combined({
		"azurerm_cognitive_account_rai_policy": {"guardrail": [{"name": "g"}]},
		"azurerm_cognitive_deployment": {"model": [{"name": "gpt-4o"}]},
	})
	count(result) == 1
}

test_azure_rai_policy_named_by_deployment_is_allowed if {
	result := deny with input as combined({
		"azurerm_cognitive_account_rai_policy": {"guardrail": [{"name": "g"}]},
		"azurerm_cognitive_deployment": {"model": [{"rai_policy_name": "${var.create_content_filter ? azurerm_cognitive_account_rai_policy.guardrail[0].name : null}"}]},
	})
	count(result) == 0
}

# --- GCP ------------------------------------------------------------------

test_gcp_template_without_floorsetting_is_denied if {
	result := deny with input as combined({"google_model_armor_template": {"guardrail": [{"template_id": "g"}]}})
	count(result) == 1
}

test_gcp_template_with_floorsetting_is_allowed if {
	result := deny with input as combined({
		"google_model_armor_template": {"guardrail": [{"template_id": "g"}]},
		"google_model_armor_floorsetting": {"guardrail": [{"enable_floor_setting_enforcement": true}]},
	})
	count(result) == 0
}

# --- No guardrail at all --------------------------------------------------

# A tree that creates no guardrail (create_guardrail = false) must not be denied for the
# absence of wiring around a resource that does not exist.
test_no_guardrail_resources_is_allowed if {
	result := deny with input as combined({"aws_lambda_function": {"tool": [{"function_name": "t"}]}})
	count(result) == 0
}

# --- Snowflake --------------------------------------------------------------

test_snowflake_ungranted_wrapper_is_denied if {
	result := deny with input as combined({"snowflake_procedure_sql": {"complete_guarded": [{"name": "COMPLETE_GUARDED"}]}})
	count(result) == 1
}

test_snowflake_granted_wrapper_is_allowed if {
	result := deny with input as combined({
		"snowflake_procedure_sql": {"complete_guarded": [{"name": "COMPLETE_GUARDED"}]},
		"snowflake_grant_privileges_to_account_role": {"complete_to_orchestrator": [{"on_schema_object": [{"object_name": "${local.complete_signature}"}]}]},
	})
	count(result) == 0
}

# A grant naming some other procedure must not satisfy the wiring check.
test_snowflake_grant_on_another_procedure_is_denied if {
	result := deny with input as combined({
		"snowflake_procedure_sql": {"complete_guarded": [{"name": "COMPLETE_GUARDED"}]},
		"snowflake_grant_privileges_to_account_role": {"other": [{"on_schema_object": [{"object_name": "${local.read_signatures[\"retrieve\"]}"}]}]},
	})
	count(result) == 1
}

test_snowflake_cortex_to_tool_owner_is_allowed if {
	result := deny with input as combined({"snowflake_grant_database_role": {"cortex": [{
		"database_role_name": "SNOWFLAKE.CORTEX_USER",
		"parent_role_name": "${var.tool_owner_role}",
	}]}})
	count(result) == 0
}

test_snowflake_cortex_to_orchestrator_is_denied if {
	result := deny with input as combined({"snowflake_grant_database_role": {"cortex": [{
		"database_role_name": "SNOWFLAKE.CORTEX_USER",
		"parent_role_name": "${var.orchestrator_role}",
	}]}})
	count(result) == 1
}
