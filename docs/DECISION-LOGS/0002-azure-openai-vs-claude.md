# ADR 0002 — Azure calls Azure OpenAI while the other two trees call Claude

**Status: Accepted** · Decided 2026-08-07 · Confirmed 2026-08-14 · Scope: `infra/terraform-azure/`

## Context

Two of the three trees call Claude. The AWS `reason` handler calls it on Bedrock; the GCP one
calls it on Vertex, where
[`modules/model-integration/variables.tf:12`](../../infra/terraform-gcp/modules/model-integration/variables.tf)
documents `claude-opus-4-5@20251101` as the model identifier shape.

Azure could serve Claude too, through the Azure AI model catalog. It does not. It provisions
Azure OpenAI and deploys `gpt-4o` by default. That is the single largest cross-tree divergence
in the repository, and it is deliberate.

The reason is the guardrail. Each tree needs one content filter that Terraform owns end to end,
because a control that has to be clicked into place after apply is a control that is missing
from half the environments:

| Tree | Filter | Terraform resource |
|---|---|---|
| AWS | Bedrock guardrail | `aws_bedrock_guardrail` + `aws_bedrock_guardrail_version` ([`modules/security/main.tf:112`](../../infra/terraform-aws/modules/security/main.tf)) |
| GCP | Vertex AI safety floor setting | project-wide, enforced on every `generateContent` |
| Azure | Responsible AI policy | `azurerm_cognitive_account_rai_policy` ([`modules/model-integration/main.tf:112`](../../infra/terraform-azure/modules/model-integration/main.tf)) |

`azurerm_cognitive_account_rai_policy` is the only Azure content filter that is a first-class
Terraform resource and the closest analogue to `aws_bedrock_guardrail`. It binds to an
`azurerm_cognitive_deployment` — an Azure OpenAI deployment. Serving Claude through the model
catalog instead would keep the vendor consistent across all three trees and give that up; the
catalog's `azurerm` coverage is thin enough that parts of it need `azapi`.

## Decision

Azure deploys Azure OpenAI. Accept model-vendor inconsistency across the three trees in
exchange for a content filter that Terraform provisions, binds, and diffs.

The trade is stated in the handler that makes the call rather than left to be discovered in the
imports — see the header of
[`infra/terraform-azure/src/reason/handler.py`](../../infra/terraform-azure/src/reason/handler.py).

## Consequences

- **The contract does not diverge, only the vendor does.** The proposal schema, the untrusted
  document handling, and the usage reporting are identical in all three trees, because they are
  properties of the architecture rather than of the model.
- **The filter is real only when bound.** An unattached `rai_policy` exists, shows up in the
  portal, looks like a control, and filters nothing. `rai_policy_name` on
  `azurerm_cognitive_deployment.model` is the line that makes it apply, and the module comment
  above the policy says so.
- `base_policy_name` names Microsoft's default explicitly, so a change to the Azure-side default
  arrives as a Terraform diff rather than being absorbed silently.
- `version_upgrade_option` is off by default. Azure retires model versions on a published
  schedule and auto-upgrade moves the deployment when that happens; a model that changes
  underneath a prompt-versioned reasoning step makes results non-reproducible, and the trace
  record would attribute the change to nothing.
- `deployment_capacity` — tokens per minute, in thousands — is the closest thing to a spend
  ceiling the model layer has. An agent in a retry loop is bounded by throughput before it is
  bounded by the daily cost alarm, which only fires after the money is spent.
- **Anyone benchmarking the three trees against each other is comparing two models**, not three
  deployments of one. Cost per execution, latency, and refusal behaviour are not comparable
  across trees, and no document in this repository should present them as if they were.

## Alternatives considered

1. **Claude through the Azure AI model catalog.** Keeps vendor parity across all three trees.
   Rejected: it loses the first-class content filter and needs `azapi` for parts of the
   deployment, which puts the guardrail outside the provider that manages everything around it.
2. **Azure OpenAI with no content filter.** Rejected — the filter is the entire reason this tree
   is on Azure OpenAI. Without it the divergence buys nothing.
3. **Drop the Azure tree and ship two clouds.** Rejected; the three-cloud parity goal is the
   point of `infra/`, and Azure is where the most instructive differences live.

## What would reopen this

`azurerm` gaining first-class coverage for a Claude catalog deployment *and* an attachable
content filter on it. At that point the divergence costs more than it buys and the tree should
move, keeping the same handler contract.
