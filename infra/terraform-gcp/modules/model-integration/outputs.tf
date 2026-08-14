output "model_id" {
  description = "Model identifier for handler configuration."
  value       = var.model_id
}

output "vertex_location" {
  description = "Region handlers should target for Vertex AI calls."
  value       = var.location
}

output "vertex_endpoint" {
  description = "Regional Vertex AI endpoint host."
  value       = "${var.location}-aiplatform.googleapis.com"
}

output "guardrail_template_id" {
  description = "Full resource name of the Model Armor template, or null when the guardrail is disabled. Handlers pass this to sanitizeUserPrompt and sanitizeModelResponse."
  value       = var.create_guardrail ? google_model_armor_template.guardrail[0].id : null
}

output "guardrail_template_name" {
  description = "Short template ID, for the handler's MODEL_ARMOR_TEMPLATE environment variable."
  value       = var.create_guardrail ? google_model_armor_template.guardrail[0].template_id : null
}

output "guardrail_enforced_by_platform" {
  description = <<-EOT
    Whether Vertex AI applies the filters on every generateContent in this project, or only
    when a handler asks for them.

    False means the guardrail is opt-in by construction: a handler that omits the sanitize
    call reaches the model unfiltered and nothing reports it. Surfaced as an output so that
    fact is assertable in review rather than inferred from a variable default.
  EOT
  value       = var.create_guardrail && var.create_floor_setting && var.floor_setting_block
}
