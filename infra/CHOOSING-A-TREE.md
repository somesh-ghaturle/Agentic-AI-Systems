# Choosing a tree

Four trees deploy the same architecture and enforce the same property. This page is for the
one decision every other document in `infra/` assumes you have already made.

**Snowflake is not a fourth option in the same sense as the other three.** It is a data
platform that runs *on* AWS, Azure or GCP — so the real question it answers is not "which
cloud" but "is my agent's data already in Snowflake". §0 below is about that; everything
after it compares the three infrastructure trees.

It does not restate those documents. Where a difference is already explained somewhere, this
page says what it means *for the choice* and links to the explanation. Five documents already
compare the trees on some axis — [`MODULES.md`](MODULES.md) on modules,
[`docs/THREAT-MODEL.md`](../docs/THREAT-MODEL.md) §6 on adversaries, the root
[`README.md`](../README.md) on services, and the Azure and GCP `ARCHITECTURE.md` files on
divergence from AWS. None of them answers "which one do I start from."

---

## The short answer

| If this is true of you | Start with | Because |
|---|---|---|
| You want the strongest write boundary and can get `roles/iam.denyAdmin` | **GCP** | The only tree whose boundary survives a later broad grant — a deny policy evaluates before allow policies. [THREAT-MODEL §6](../docs/THREAT-MODEL.md) |
| You want two independent locks and the fewest prerequisites outside the account | **AWS** | An identity policy *and* a resource policy, each refusing on its own. Nothing needed outside the AWS account |
| You are already on Azure, or you need a first-class Terraform content filter | **Azure** | `azurerm_cognitive_account_rai_policy` has no counterpart on the other two. Know what you are trading — see §2 |
| You are reading to learn the architecture rather than to deploy it | **AWS** | It is the baseline the other two document their divergence *from*, so it reads without cross-references |
| Your agent's data already lives in Snowflake, and the tools are queries over it | **Snowflake** | The tools *are* the data platform. No egress, no second copy, no sync to fall behind — at the cost of §0's trade |

If none of those decide it, take AWS. It has the fewest things that can stop an apply before
it starts, which §1 is about.

---

## 0 · Whether Snowflake is even the question

Pick this tree when the agent's read tools are queries over data that is already in
Snowflake. That is a real and common shape — the retrieval corpus, the business tables the
write tools modify, and the audit trail all live in one place, so there is no export, no
second copy, and no ingestion path to fall behind. `modules/knowledge` is the clearest case:
Cortex Search indexes a *query*, not a snapshot, so the staleness failure the other three
trees can have simply does not exist here.

What you give up is the part that has nothing to do with data:

| | The three infrastructure trees | Snowflake |
|---|---|---|
| Approval flow | Execution suspends, resumes on a callback | **Polls.** A Task is a scheduler; approvals wait for the next sweep |
| Arbitrary compute | Any runtime, any dependency | Stored procedures, or Snowpark Container Services at a compute-pool cost |
| Network isolation | VPC / VNet / VPC-SC | Account allow-list only; PrivateLink is a separate purchase |
| Blast radius of the deploy role | Scoped cloud IAM | `CREATE ROLE` at account level — it builds the role graph, so it can rebuild it |

The approval row is the one that decides most cases. If a human approval must be acted on in
seconds rather than on a sweep interval, this is the wrong tree, and the answer is one of the
other three with Snowflake as the data layer behind it.

The write boundary itself is not a trade. It is as strong here as anywhere — arguably
simpler, since there is no policy evaluation order to get wrong — but it is made of role
inheritance, which is easier to break by accident. See
[`terraform-snowflake/README.md`](terraform-snowflake/README.md) § "The write boundary".

---

## 1 · What you need before you can apply anything

**This is the strongest input to the decision and the one most likely to be discovered late.**
Each tree's `HOW-TO-DEPLOY.md` carries its own prerequisites; nothing until now put them side
by side. Two of the three need something that project or subscription admin does not include.

| | AWS | Azure | GCP |
|---|---|---|---|
| Terraform | ≥ 1.6 | ≥ 1.6 | ≥ 1.6 |
| Cloud permissions | Create IAM roles, Lambda, Step Functions, DynamoDB, S3, OpenSearch Serverless, KMS, SNS, CloudWatch | Create RGs, Storage, Key Vault, Cosmos, Log Analytics, Service Bus, Search, Functions, Logic Apps | Project Owner or Editor |
| **Needed beyond that** | *Nothing* | **Entra directory role — at least Application Developer** | **`roles/iam.denyAdmin`**, project or org level |
| Why | — | The read/write split is enforced by Entra app roles, so the apply registers one application per tool. A subscription Contributor without directory permissions cannot do it | Creates the IAM Deny policy. Without it the apply fails at the **very last resource**, after everything else exists |
| Manual console step | None | None | **Accept Anthropic's Model Garden terms** in the target project. No Terraform resource, no API. Skip it and every model call returns 403 with a message that does not say why |
| Environment isolation | One account works | One subscription works | **One project per environment, not a preference** — `roles/datastore.user` covers every Firestore database in the project, service account IDs are project-unique, and a Deny policy attaches to the project |
| API enablement | Automatic | Automatic | Only `aiplatform.googleapis.com` is enabled by the tree; enable the other eleven yourself |
| Remote state prerequisite | An S3 bucket and a DynamoDB table | A storage account | A GCS bucket |

Full detail: [AWS](terraform-aws/HOW-TO-DEPLOY.md) · [Azure](terraform-azure/HOW-TO-DEPLOY.md) ·
[GCP](terraform-gcp/HOW-TO-DEPLOY.md).

**Decisions that cannot be changed after the first apply,** because they recreate resources:

| Tree | One-way |
|---|---|
| AWS | Object Lock on the archive (S3 cannot enable it on an existing bucket), `project` name, region |
| Azure | `project` name — Cosmos and storage accounts cap at 24 characters, and the variable validation keeps the longest generated name inside it |
| GCP | `project` name, capped at **10 characters** — the ceiling is the 30-character service account ID limit, and it is set by `prod` because `prod` is a character longer than `dev` |

---

## 2 · The boundary, and the one row where the three differ

All three enforce it: a state-changing action cannot reach production without a human
approving that specific action, and the identity platform enforces it rather than the prompt.
What differs is what happens when someone *later* widens a grant.

[`docs/THREAT-MODEL.md`](../docs/THREAT-MODEL.md) §6 is the authority and is not repeated here.
The row that decides between trees is the second one in its table:

- **AWS** — two allow-shaped locks: an identity policy and a Lambda resource policy. Remove
  either and the other still refuses. A later broad invoke grant **reopens the path**.
- **Azure** — one load-bearing line, `app_role_assignment_required = true`, plus two
  mitigations. Azure has no Function resource policy and no way to govern Entra objects with
  Azure Policy, so the second lock is not available at any price. A CI check and
  `modules/entra-audit` guard the line rather than replacing it. This is genuinely thinner
  and [Azure's ARCHITECTURE.md §2](terraform-azure/ARCHITECTURE.md) says so plainly.
- **GCP** — one allow and one **deny**. Deny rules evaluate before allow policies, so a later
  broad grant cannot reopen the path. It is the only override-proof lock of the three.

Azure buys one thing back that neither other tree has: `modules/entra-audit` detects a cloud
admin acting out of band, which THREAT-MODEL §6 records as "not defended" on AWS and GCP.

---

## 3 · The model layer

The one place the trees diverge on vendor, and a deliberate trade rather than drift.

| | AWS | Azure | GCP |
|---|---|---|---|
| Model | Claude, on Bedrock | Azure OpenAI | Claude, on Vertex AI |
| Content filter | Bedrock guardrail, in `modules/security` | `azurerm_cognitive_account_rai_policy` | Guardrail config in `modules/model-integration` |

Azure's choice buys `azurerm_cognitive_account_rai_policy` — the only Azure content filter
that is a first-class Terraform resource, and the closest analogue to a Bedrock guardrail — at
the cost of model consistency across the three trees. Serving Claude through the Azure AI model
catalog instead reverses both halves of that trade.

If you need the same model on all three, that is AWS and GCP today and Azure with rework.

---

## 4 · What each tree does not have

Module counts differ because the clouds need different things, not because a tree is
unfinished. `MODULES.md` catalogues all of them; this is only what is *absent* and why.

| Module | AWS | Azure | GCP | Note |
|---|---|---|---|---|
| `approval`, `archive`, `knowledge`, `observability`, `orchestration`, `security`, `state`, `tools` | ✅ | ✅ | ✅ | The eight every tree has |
| `identity` | — | ✅ | ✅ | AWS computes role ARNs in `locals` because they are deterministic. GCP service account emails are deterministic too, but GCP accepts IAM bindings to service accounts that do not exist, so a constructed email would be correct and unverified |
| `model-integration` | — | ✅ | ✅ | AWS has none — its Bedrock guardrail is a security control and lives in `modules/security` |
| `networking` | — | ✅ | — | Azure only. A VNet and subnet, wired to exactly one thing: an optional private endpoint on AI Search in prod |
| `entra-audit` | — | ✅ | — | Azure only, and it exists *because* the boundary there is one lock |
| **Total** | **8** | **12** | **10** | |

Environment roots: AWS `dev`/`staging`/`prod`, GCP `dev`/`staging`/`prod`, Azure the same plus
`envs/tenant` — a fourth root because the Entra audit alert it applies is tenant-scoped, and two
roots managing it would revert each other.

**None of the three ships private networking for the handlers.** No AWS Lambda has a
`vpc_config`, no GCP function has a VPC connector, and Azure's Function Apps are not
VNet-integrated even on EP1. Every handler is reached over a public endpoint and authorized by
identity. That is a deliberate choice for a reference deployment, recorded with its reasoning in
[`.checkov.yaml`](../.checkov.yaml), and it is the first thing to change for production.

**That transition is not documented in this repository.** It is a different deployment — private
endpoints, private DNS zones, NAT or interface endpoints for every service the handlers call —
and none of the three trees ships it. The nearest thing here is the note above the network policy
in [`terraform-aws/modules/knowledge/main.tf`](terraform-aws/modules/knowledge/main.tf), which
works through one concrete consequence: prod locks the knowledge collection to a VPC endpoint
that no handler can reach, so the strict setting is declared rather than exercised.

---

## 5 · What runs when nothing is happening

This page carries no pricing. What it can tell you is which resources in each tree have **no
scale-to-zero**, because that is a property of the HCL rather than of a price list.

- **GCP** — the Vertex AI index endpoint is deployed with `min_replica_count = 1` and no
  autoscaling. `envs/dev/main.tf` names it directly: *"A deployed index has no scale-to-zero,
  which makes this the largest standing cost in the tree."* Dev keeps it at the floor.
- **Azure** — `dev` runs Function Apps on `Y1`, the Consumption plan. `prod` moves to `EP1`,
  Elastic Premium, which is a provisioned tier rather than a consumption one. The tree's own
  variable description gives the reason: `Y1` cannot join a VNet, so private endpoints are
  unavailable on it.
- **AWS** — the tree makes no standing-cost claim, and this page will not invent one. Lambda
  and Step Functions bill on use; OpenSearch Serverless capacity is not configured by these
  modules.

Treat this section as a pointer to where to look, not as a cost model.

---

## 6 · What this page deliberately does not decide

- **Price.** No tree here is costed, and the three are not comparable without your traffic
  shape, region, and retention policy.
- **Region and service availability.** Every service named above exists in some regions and not
  others, and model availability is separately regional — the GCP tree keeps `vertex_location`
  distinct from `region` for exactly that reason.
- **Your organization's policy.** A landing zone that forbids public function endpoints, or an
  Entra tenant that will not grant Application Developer, decides this before any of the above
  does.
- **The security ranking under attack.** That is [THREAT-MODEL](../docs/THREAT-MODEL.md)'s job,
  and §2 links to it rather than restating its table.

---

## Where to read next

| You want | Read |
|---|---|
| The architecture in one cloud's own terms, with diagrams | `terraform-{aws,azure,gcp}/ARCHITECTURE.md` |
| Ordered deploy steps and prerequisites | `terraform-{aws,azure,gcp}/HOW-TO-DEPLOY.md` |
| Every module, its dependencies and status | [MODULES.md](MODULES.md) |
| What an adversary reaches, and which cloud survives it | [docs/THREAT-MODEL.md](../docs/THREAT-MODEL.md) |
| How Azure and GCP differ from the AWS baseline, in detail | The "Divergences from the AWS tree" section in each of their `ARCHITECTURE.md` |
| Why the checks that gate all three are shaped the way they are | [docs/HARDENING-PLAN.md](../docs/HARDENING-PLAN.md) |

---

## Verify

Every count and claim of absence in this page is checkable:

```bash
# §4 — module counts and which tree lacks which module
for c in aws azure gcp; do
  echo "$c: $(ls infra/terraform-$c/modules | wc -l) modules"
  ls infra/terraform-$c/modules
done

# §4 — environment roots, including Azure's fourth
ls -d infra/terraform-*/envs/*/

# §4 — no handler in any tree has private networking
grep -rn "vpc_config" infra/terraform-aws/modules/                       # no matches
grep -rn "vpc_connector\|vpc_access" infra/terraform-gcp/modules/        # no matches
grep -rn "virtual_network_subnet_id" infra/terraform-azure/modules/      # knowledge only

# §5 — the GCP index endpoint floor, and the Azure plan SKUs
grep -rn "min_replica_count" infra/terraform-gcp/envs/*/main.tf
grep -rn "service_plan_sku" infra/terraform-azure/envs/*/main.tf
```
