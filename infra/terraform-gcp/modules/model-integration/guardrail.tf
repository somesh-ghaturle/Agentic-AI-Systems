# The guardrail — Model Armor.
#
# terraform-aws/modules/security creates an `aws_bedrock_guardrail` and states its status
# plainly, which is worth repeating here verbatim because it applies unchanged:
#
#   "a mitigation layer, not the control. Worth having: it catches a meaningful share of
#    injection attempts and PII leakage cheaply. Worth being honest about: a determined
#    injection will get past it, which is exactly why the write path is gated separately."
#
# Model Armor is the closest of the three clouds' guardrail products to the Bedrock one,
# and on one axis it is ahead: it covers responsible-AI categories, prompt-injection and
# jailbreak detection, malicious URIs, and — through Sensitive Data Protection — the PII
# inspection that the Azure tree has no equivalent for at all.
#
# ---------------------------------------------------------------------------
# Two ways to apply it, and only one of them is a control
# ---------------------------------------------------------------------------
#
# **The template** is a named policy that a caller passes to `sanitizeUserPrompt` and
# `sanitizeModelResponse`. It filters what it is asked to filter. A handler that forgets
# the call — or a new handler written by someone who did not know about it — reaches the
# model unfiltered, and nothing reports that. The template is opt-in by construction.
#
# **The floor setting** is enforced by Vertex AI itself on every `generateContent` in the
# project, whether or not the caller asked. That is the difference between a guardrail the
# code chooses to use and a guardrail the code cannot skip, and it is the same distinction
# this tree draws everywhere else between a convention and a boundary.
#
# Both are created here. The floor setting is opt-in (`create_floor_setting`) because it
# applies to every Vertex AI call in the project including ones this tree did not create,
# which is exactly the reach that makes it effective and exactly the reason it should not
# switch itself on in a shared project.
# ---------------------------------------------------------------------------

resource "google_project_service" "modelarmor" {
  count = var.manage_api_enablement && var.create_guardrail ? 1 : 0

  project = var.project_id
  service = "modelarmor.googleapis.com"

  # Same reasoning as aiplatform: disabling a project-level API because one environment was
  # torn down breaks every other environment sharing the project.
  disable_on_destroy = false
}

resource "google_model_armor_template" "guardrail" {
  count = var.create_guardrail ? 1 : 0

  project     = var.project_id
  location    = var.guardrail_location
  template_id = "${replace(var.name_prefix, "_", "-")}-guardrail"

  filter_config {
    # The one that matters most for an agentic system. Retrieved documents reach the model
    # as data and can carry text phrased as instructions; the retrieve tool labels them
    # untrusted and the reason handler wraps them in tags, and this is the third layer.
    #
    # None of the three is the control. The write boundary is.
    pi_and_jailbreak_filter_settings {
      filter_enforcement = "ENABLED"
      confidence_level   = var.jailbreak_confidence_level
    }

    # A model that has been talked into emitting a link is a model that can exfiltrate the
    # conversation to whoever owns the domain.
    malicious_uri_filter_settings {
      filter_enforcement = "ENABLED"
    }

    rai_settings {
      dynamic "rai_filters" {
        for_each = var.rai_filters
        content {
          filter_type      = rai_filters.value.filter_type
          confidence_level = rai_filters.value.confidence_level
        }
      }
    }

    # PII inspection at the model boundary. PRODUCTION-PRINCIPLES.md is specific that
    # masking happens before data reaches the model — this is the backstop for what upstream
    # masking misses, not a replacement for it.
    #
    # `basic_config` uses SDP's built-in infotypes and needs no other resource.
    # `advanced_config` takes DLP templates, which is what you want once "PII" means
    # something specific to your data rather than the default set.
    dynamic "sdp_settings" {
      for_each = var.sdp_mode == "none" ? [] : [1]
      content {
        dynamic "basic_config" {
          for_each = var.sdp_mode == "basic" ? [1] : []
          content {
            filter_enforcement = "ENABLED"
          }
        }

        dynamic "advanced_config" {
          for_each = var.sdp_mode == "advanced" ? [1] : []
          content {
            inspect_template    = var.sdp_inspect_template
            deidentify_template = var.sdp_deidentify_template
          }
        }
      }
    }
  }

  template_metadata {
    # Sanitize operations are the evidence behind a refusal. Without them a blocked request
    # is indistinguishable from a broken one, and the first real injection attempt leaves no
    # trace that it happened.
    log_sanitize_operations = true
    log_template_operations = true

    # False on purpose. If a filter cannot run, the request is failed rather than passed
    # through unfiltered — a guardrail that fails open under load is a guardrail that is
    # absent exactly when the system is under stress.
    ignore_partial_invocation_failures = false

    multi_language_detection {
      # Injection written in another language is still injection, and the filters are
      # English-first without this.
      enable_multi_language_detection = true
    }
  }

  labels = var.labels

  depends_on = [google_project_service.modelarmor]
}

# ---------------------------------------------------------------------------
# The floor setting — the same filters, enforced by Vertex AI rather than by the caller
#
# `inspect_and_block` is what makes this a control. `inspect_only` logs what it would have
# blocked and blocks nothing, which is the right way to roll this out and the wrong way to
# leave it: a floor setting in inspect-only mode appears in the console, reads as enabled,
# and stops nothing.
# ---------------------------------------------------------------------------

resource "google_model_armor_floorsetting" "guardrail" {
  count = var.create_guardrail && var.create_floor_setting ? 1 : 0

  parent   = "projects/${var.project_id}"
  location = var.guardrail_location

  enable_floor_setting_enforcement = true

  ai_platform_floor_setting {
    enable_cloud_logging = true

    # Exactly one of these may be true. Blocking is the point; inspect_only is a rollout
    # position, not a destination.
    inspect_and_block = var.floor_setting_block
    inspect_only      = !var.floor_setting_block
  }

  filter_config {
    pi_and_jailbreak_filter_settings {
      filter_enforcement = "ENABLED"
      confidence_level   = var.jailbreak_confidence_level
    }

    malicious_uri_filter_settings {
      filter_enforcement = "ENABLED"
    }

    rai_settings {
      dynamic "rai_filters" {
        for_each = var.rai_filters
        content {
          filter_type      = rai_filters.value.filter_type
          confidence_level = rai_filters.value.confidence_level
        }
      }
    }
  }

  depends_on = [google_project_service.modelarmor]
}
