# Orchestration — the workflow, and the suspension that makes the gate real
#
# ---------------------------------------------------------------------------
# Why a Logic App and not Durable Functions
# ---------------------------------------------------------------------------
#
# The AWS design suspends the run on a Step Functions task token: genuinely parked, with
# the state persisted by the platform rather than by handler code, for as long as the
# approval window allows.
#
# The only Azure primitive with that shape is a Logic App `HttpWebhook` action. It posts a
# subscribe request carrying a callback URL, then stops. Nothing polls, nothing sleeps,
# and no code of ours holds the state. Durable Functions can approximate it with an
# external event, but the orchestration state then lives in a storage account our code
# manages, which moves a correctness property out of the platform and into code that has
# to be right.
#
# ---------------------------------------------------------------------------
# Why the definition is built in `locals` rather than read from a JSON file
# ---------------------------------------------------------------------------
#
# The AWS side templates a `.json.tftpl` because ASL is passed to the state machine as
# one opaque string. Logic App actions are separate Terraform resources, so building the
# bodies with `jsonencode` keeps every interpolated URL and audience type-checked at plan
# time. A typo'd tool name in a template file surfaces as a 404 at runtime; here it fails
# to plan.
#
# Actions with branches nest their children inside the parent's body — that is the Logic
# App schema, not a choice. So `CheckLoopBound` carries the whole gated path inside it.

locals {
  # Managed identity auth for every outbound call. No keys, no shared secrets — the
  # workflow presents a token minted for the specific audience it is calling, and the
  # target's Easy Auth rejects anything else.
  #
  # `audience` is not optional here even though Azure will accept the call without it:
  # omitted, the platform requests a token for the ARM audience, which the tool's Easy
  # Auth correctly refuses. That failure reads as a permissions problem and is not one.
  auth = { for name, audience in var.tool_audiences : name => {
    type     = "ManagedServiceIdentity"
    identity = var.orchestrator_identity.id
    audience = audience
  } }

  trace_auth = {
    type     = "ManagedServiceIdentity"
    identity = var.orchestrator_identity.id
    audience = var.trace_emitter.audience
  }

  # A trace call, parameterized by event type. Every terminal path writes one — an
  # outcome nobody recorded is an outcome nobody can audit, which is why the trace
  # emitter is a required input here rather than an optional one.
  trace_action = {
    type = "Http"
    inputs = {
      method         = "POST"
      uri            = var.trace_emitter.url
      authentication = local.trace_auth
    }
  }
}

resource "azurerm_logic_app_workflow" "orchestrator" {
  name                = "${var.name_prefix}-orchestrator"
  location            = var.location
  resource_group_name = var.resource_group_name

  identity {
    type         = "UserAssigned"
    identity_ids = [var.orchestrator_identity.id]
  }

  # Read by the actions below via @parameters(). Kept as workflow parameters rather than
  # inlined so that an operator can see the wiring in the portal without reading
  # Terraform.
  workflow_parameters = {
    maxSteps = jsonencode({
      type         = "Int"
      defaultValue = var.max_steps
    })
  }

  parameters = {
    maxSteps = tostring(var.max_steps)
  }

  tags = var.tags
}

resource "azurerm_logic_app_trigger_http_request" "start" {
  name         = "Start"
  logic_app_id = azurerm_logic_app_workflow.orchestrator.id

  # Requests that do not carry these are rejected by the platform before any action runs,
  # which is cheaper than discovering a missing tenant_id three actions later.
  schema = jsonencode({
    type = "object"
    properties = {
      correlation_id = { type = "string" }
      tenant_id      = { type = "string" }
      request        = { type = "string" }
    }
    required = ["correlation_id", "tenant_id", "request"]
  })
}

# ---------------------------------------------------------------------------
# The read path
# ---------------------------------------------------------------------------

resource "azurerm_logic_app_action_custom" "retrieve" {
  name         = "Retrieve"
  logic_app_id = azurerm_logic_app_workflow.orchestrator.id

  body = jsonencode({
    type = "Http"
    inputs = {
      method = "POST"
      uri    = var.read_tool_urls["retrieve"]
      body = {
        tenant_id = "@triggerBody()?['tenant_id']"
        query     = "@triggerBody()?['request']"
      }
      authentication = local.auth["retrieve"]
    }
    runAfter = {}
  })

  depends_on = [azurerm_logic_app_trigger_http_request.start]
}

# Retrieval failing is degraded, not fatal — the model can answer without context, and
# refusing to try turns a partial outage into a total one. `runAfter` accepts both
# outcomes, which is what makes this a fallback rather than a second attempt.
resource "azurerm_logic_app_action_custom" "reason" {
  name         = "Reason"
  logic_app_id = azurerm_logic_app_workflow.orchestrator.id

  body = jsonencode({
    type = "Http"
    inputs = {
      method = "POST"
      uri    = var.read_tool_urls["reason"]
      body = {
        tenant_id = "@triggerBody()?['tenant_id']"
        request   = "@triggerBody()?['request']"

        # Null when Retrieve failed. The handler must treat absent context as "answer
        # without it", not as an error.
        context = "@body('Retrieve')?['documents']"
      }
      authentication = local.auth["reason"]
    }
    runAfter = {
      (azurerm_logic_app_action_custom.retrieve.name) = ["Succeeded", "Failed", "Skipped"]
    }
  })

  depends_on = [azurerm_logic_app_action_custom.retrieve]
}

# ---------------------------------------------------------------------------
# The bound, the gate, and everything downstream of them
#
# Nested because Logic App branch actions carry their children in their own body. Read
# this as the flowchart in ARCHITECTURE.md section 3.
# ---------------------------------------------------------------------------

resource "azurerm_logic_app_action_custom" "check_loop_bound" {
  name         = "CheckLoopBound"
  logic_app_id = azurerm_logic_app_workflow.orchestrator.id

  body = jsonencode({
    type = "If"

    # Checked before anything else downstream. An agent that loops is an agent spending
    # money, and exceeding the budget is a failure — not a quiet stop that returns a
    # partial answer as though it were complete.
    expression = {
      and = [
        { greater = ["@int(coalesce(body('Reason')?['step'], 0))", "@parameters('maxSteps')"] }
      ]
    }

    actions = {
      LoopBoundExceeded = merge(local.trace_action, {
        inputs = merge(local.trace_action.inputs, {
          body = {
            event_type     = "loop_bound_exceeded"
            correlation_id = "@triggerBody()?['correlation_id']"
            step           = "@body('Reason')?['step']"
          }
        })
        runAfter = {}
      })

      FailExecution = {
        type = "Terminate"
        inputs = {
          runStatus = "Failed"
          runError = {
            code    = "LoopBoundExceeded"
            message = "Step budget exhausted before the request completed."
          }
        }
        runAfter = { LoopBoundExceeded = ["Succeeded", "Failed"] }
      }
    }

    else = {
      actions = {
        # Deterministic checks — ownership, permission, limits — before a human is ever
        # asked. This is what keeps approval requests meaningful: a reviewer shown mostly
        # junk stops reading, and gate fatigue is how a gate fails while still appearing
        # to work.
        ValidateProposal = {
          type = "Http"
          inputs = {
            method = "POST"
            uri    = var.validator_url
            body = {
              mode           = "validate"
              correlation_id = "@triggerBody()?['correlation_id']"
              tenant_id      = "@triggerBody()?['tenant_id']"
              proposal       = "@body('Reason')?['proposal']"
            }
            authentication = {
              type     = "ManagedServiceIdentity"
              identity = var.orchestrator_identity.id
              audience = var.validator_audience
            }
          }
          runAfter = {}
        }

        ValidationOutcome = {
          type = "If"

          expression = {
            and = [
              { equals = ["@body('ValidateProposal')?['valid']", true] }
            ]
          }

          actions = {
            # The suspension. `subscribe` hands the validator a callback URL and the run
            # stops here — genuinely parked, not polling. The executor resolves it after
            # claiming the record and invoking the write tool.
            AwaitHumanApproval = {
              type = "HttpWebhook"
              inputs = {
                subscribe = {
                  method = "POST"
                  uri    = var.validator_url
                  body = {
                    mode           = "request_approval"
                    correlation_id = "@triggerBody()?['correlation_id']"
                    tenant_id      = "@triggerBody()?['tenant_id']"
                    proposal       = "@body('Reason')?['proposal']"
                    callback_url   = "@{listCallbackUrl()}"
                  }
                  authentication = {
                    type     = "ManagedServiceIdentity"
                    identity = var.orchestrator_identity.id
                    audience = var.validator_audience
                  }
                }

                # Nothing to tear down: the record's terminal state is the unsubscribe.
                unsubscribe = {}
              }

              # The window. When it closes with no answer, the action fails and the
              # timeout branch below runs — which is a different event from a human
              # declining, and is tracked separately for exactly that reason.
              limit = { timeout = var.approval_timeout }

              runAfter = {}
            }

            RecordSuccess = merge(local.trace_action, {
              inputs = merge(local.trace_action.inputs, {
                body = {
                  event_type     = "request_complete"
                  correlation_id = "@triggerBody()?['correlation_id']"
                  outcome        = "approved"
                  cost_usd       = "@body('Reason')?['cost_usd']"
                  total_tokens   = "@body('Reason')?['total_tokens']"
                }
              })
              runAfter = { AwaitHumanApproval = ["Succeeded"] }
            })

            # Nobody answered. Caught separately from a rejection because conflating them
            # makes reviewer disengagement invisible — the gate looks like it is working
            # right up until nobody is reading it.
            ApprovalAbandoned = merge(local.trace_action, {
              inputs = merge(local.trace_action.inputs, {
                body = {
                  event_type     = "approval_abandoned"
                  correlation_id = "@triggerBody()?['correlation_id']"
                  outcome        = "abandoned"
                }
              })
              runAfter = { AwaitHumanApproval = ["Failed", "TimedOut"] }
            })
          }

          else = {
            actions = {
              # Rejected before notification. No human was troubled by this one.
              RecordRejection = merge(local.trace_action, {
                inputs = merge(local.trace_action.inputs, {
                  body = {
                    event_type     = "request_complete"
                    correlation_id = "@triggerBody()?['correlation_id']"
                    outcome        = "rejected_by_validator"
                    reason         = "@body('ValidateProposal')?['reason']"
                  }
                })
                runAfter = {}
              })
            }
          }

          runAfter = { ValidateProposal = ["Succeeded"] }
        }
      }
    }

    runAfter = { Reason = ["Succeeded"] }
  })

  depends_on = [azurerm_logic_app_action_custom.reason]
}
