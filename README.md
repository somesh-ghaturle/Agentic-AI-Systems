# Agentic AI Systems

This repository is a curated reference hub for **systematic AI enterprise systems** (including agentic approaches), with a focus on practical deployment patterns, architecture choices, governance, and production considerations.

## What this repository covers

- Agentic system architecture patterns
- Deployment-oriented design references
- Tool orchestration, memory, and context engineering concepts
- Security and reliability guidance for production workflows
- Governance, lifecycle, and reproducibility for enterprise AI

## Curated references

- [all-agentic-architectures (FareedKhan-dev)](https://github.com/FareedKhan-dev/all-agentic-architectures) — production-grade architecture library and runnable examples.
- [GitHub All-Stars #5: deepagents](https://medium.com/) — deep reasoning architecture discussion, including virtual file-system style memory.
- [agentic-ai-architecture topic on GitHub](https://github.com/topics/agentic-ai-architecture) — broad architecture-focused repositories and references.
- [alirezadir/Agentic-AI-Systems](https://github.com/alirezadir/Agentic-AI-Systems) — practical system design examples, tutorials, and architecture documentation.
- [Voyager architecture notebook](https://github.com/FareedKhan-dev/all-agentic-architectures/blob/main/docs/architectures/29_voyager.ipynb) — concrete architecture walkthrough example.
- [Security architecture of GitHub Agentic Workflows](https://github.blog/) — layered security model for agentic workflows.
- [agentic-ai topic on GitHub](https://github.com/topics/agentic-ai) — ecosystem-wide discovery of agentic AI projects.

## Scope note

Links above are starting points for research and implementation planning. This repository will continue evolving to include deployment templates, architecture notes, and hands-on enterprise examples.

## Purpose

This repository's main purpose is to provide practitioners and engineering teams with clear, followable architectures, runnable examples, and deployment-ready patterns so they can implement systematic AI enterprise solutions (including agentic designs) in production.

## How to use this repository

- Clone the repo and explore the architecture examples and templates.
- Start with the curated references to learn the patterns and trade-offs.
- Use the deployment templates as a baseline; adapt infrastructure and governance to your environment.
- Contribute runnable examples, post-mortems, and additional references via pull requests.

## Advanced references (examples to include)

- [LangChain](https://github.com/langchain-ai/langchain) (practical agent and orchestration patterns)
- [Ray](https://github.com/ray-project/ray) (distributed execution for agents and workloads)
- [Kubeflow](https://www.kubeflow.org/) (ML orchestration and pipelines)
- [MLflow](https://mlflow.org/) (experiment tracking and reproducibility)
- [Google MLOps: Continuous Delivery for Machine Learning](https://cloud.google.com/architecture/mlops-continuous-delivery-automation) (guide)
- [Model Cards](https://modelcards.withgoogle.com/) for model reporting (best practices for model documentation)
- [Hidden Technical Debt in Machine Learning Systems](https://papers.nips.cc/paper/5656-hidden-technical-debt-in-machine-learning-systems.pdf) (operational risks paper)

If you'd like, I can add more targeted advanced references (papers, repos, templates) for governance, security, or large-scale orchestration — tell me which areas to prioritize.

## Governance & security references

- [NIST AI Risk Management Framework](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf)
- [EU AI Act](https://commission.europa.eu/publications/eu-artificial-intelligence-act_en) (summary and compliance guidance)
- [Responsible AI practices](https://learn.microsoft.com/en-us/azure/ai/fundamentals/responsible-ai) (Microsoft)
- [Model Cards & documentation best practices](https://modelcards.withgoogle.com/)
- [OWASP AI Security Top Ten](https://owasp.org/www-project-top-ten/) (emerging guidance)

These resources provide governance, risk, and security perspectives suitable for enterprise adoption.

## System architecture reference

- **Agentic System Architecture**: [docs/agentic-system-architecture/](docs/agentic-system-architecture/README.md) — reference architecture for building agentic systems as production software. Single-agent vs. multi-agent trade-offs, the six building blocks (model routing, tool contracts, memory and state, orchestration, trace-level evals, approval gates), production engineering principles, and a design-review checklist.

## Reference infrastructure

Three parallel Terraform trees under [infra/](infra/), implementing the same agentic architecture on each cloud's own primitives. They are the deployment-ready counterpart to the architecture reference above — the six building blocks expressed as infrastructure rather than as prose.

| Tree | Orchestrator | Tools | State / approvals | Knowledge |
| --- | --- | --- | --- | --- |
| [terraform-aws/](infra/terraform-aws/) | Step Functions | Lambda | DynamoDB | OpenSearch Serverless |
| [terraform-azure/](infra/terraform-azure/) | Logic Apps | Functions | Storage Tables / Cosmos DB | AI Search |
| [terraform-gcp/](infra/terraform-gcp/) | Cloud Workflows | Cloud Functions gen2 | Firestore | Vertex AI Vector Search |

Each tree has its own `ARCHITECTURE.md` with mermaid diagrams drawn in that cloud's terms, a `HOW-TO-DEPLOY.md`, and `envs/dev` plus `envs/prod` roots. Azure has a third root, `envs/tenant`, because the Entra audit alert it applies is tenant-scoped — two roots managing it would revert each other.

**The property they all enforce:** a state-changing action cannot reach production without a human approving that specific action, and that is enforced by the identity platform — not by the prompt, and not by the model choosing to behave. Tools are split into `read` and `write`; only the approval executor can invoke a write tool, and the orchestrator cannot.

**How that boundary is drawn differs by cloud, and each tree's ARCHITECTURE.md section 2 says so plainly rather than claiming parity it does not have:**

- **AWS** — two independent locks: an identity policy and a Lambda resource policy. Remove either and the other still refuses.
- **Azure** — one load-bearing line (`app_role_assignment_required = true`) plus two mitigations. Azure has no resource-policy equivalent for Functions, so this is genuinely thinner, and a CI check and an Entra audit alert guard the line rather than replacing it.
- **GCP** — the closest to the AWS original, because a gen2 function is a Cloud Run service underneath and carries its own IAM policy. It also adds an IAM Deny policy, the only override-proof lock of the three: deny rules evaluate before allow policies, so a later broad grant cannot reopen the path.

**Status.** All seven environment roots pass `terraform validate`, and all three trees have a handler source tree (`src/`) with a build script, so each can `plan` once its packages are built — every function package path is read at plan time to compute a deployment hash, which is why `src/build.sh` runs before `terraform plan` rather than after.

The three trees are at parity in structure, not in implementation, and the differences are deliberate. Each handler tree is written against its own provider's SDK and its own failure modes: the packaging differs (AWS vendors wheels into the zip because a Lambda zip is the final artifact; Azure and GCP ship source and let Oryx and Cloud Build resolve dependencies), the approval claim differs (a DynamoDB condition expression, a Firestore transaction, a Cosmos ETag), and the trace field names differ because each provider's queries match different ones. `src/tests/` in each tree asserts its own conventions, so a handler copied between trees fails in CI rather than in production.

The model layer is the one place the trees diverge on vendor: AWS calls Claude on Bedrock and GCP calls Claude on Vertex, while Azure calls Azure OpenAI. That is a trade — it buys `azurerm_cognitive_account_rai_policy`, the only Azure content filter that is a first-class Terraform resource and the closest analogue to a Bedrock guardrail, at the cost of model consistency. Serving Claude through the Azure AI model catalog instead would reverse both halves of that trade.

## Working with coding agents

- **Agentic Coding Playbook**: [docs/agentic-coding-playbook/](docs/agentic-coding-playbook/README.md) — a drop-in kit for treating Claude (or any coding agent) as an agent inside your workflow rather than a chatbot you consult. Eight habits, a two-week ramp, named antipatterns, a team workflow for shared repos, enterprise rollout and agent-security guidance, and copy-paste templates for `CLAUDE.md`, scoped rules, slash commands, skills, and subagents.

## Included templates & checklists

- Repository audit (2026-08-14) — findings and suggested order: [docs/REPO-AUDIT.md](docs/REPO-AUDIT.md)
- Governance checklist: [docs/governance-checklist.md](docs/governance-checklist.md)
- Security checklist: [docs/security-checklist.md](docs/security-checklist.md)
- Privacy checklist: [docs/privacy-checklist.md](docs/privacy-checklist.md)
- CONTRIBUTING guidelines: [CONTRIBUTING.md](CONTRIBUTING.md)

**Worked examples** — tests, architecture notes, and no dependencies:

- [hermes-agent](examples/hermes-agent/README.md) — routing and the write boundary in application code
- [trace-eval](examples/trace-eval/README.md) — trace-level evaluation, scoring the path rather than the answer

**Applied example** — tracing, audit, provenance, and governance docs over HTTP:

- [e2e-agent](examples/e2e-agent/README.md)

**Minimal references** — short scripts showing one idea each:

- [starter-agent](examples/starter-agent/README.md) — the smallest possible agent loop
- [rag-faiss](examples/rag-faiss/README.md) — build and query a local vector index
- [rag-langchain](examples/rag-langchain/README.md) — the same, through LangChain
- [langchain-agent](examples/langchain-agent/README.md) — a minimal LangChain agent
- [ray-orchestrator](examples/ray-orchestrator/README.md) — parallel task execution with Ray

**Hermes** is the runnable counterpart to the infrastructure below. It routes a request to a handler, runs read tools on the spot, and returns anything that would change state as a proposal that stops until a human approves *that specific action* — approval bound to a fingerprint of the exact arguments, single-use, expiring. The router holds no reference to a write tool; the approval executor holds nothing else. Standard library only, no model, no cloud account, and the boundary tests were mutation-tested rather than trusted.

**trace-eval** is the feedback edge from the architecture diagram, running. It scores the same runs two ways — one grader reads the final answer, one reads the trace — and prints where they disagree. Against an agent with no write boundary, it finds three requests where the answer was on topic, helpful, and graded PASS while a production service was restarted with nobody's authorisation. Whether a human approved an action is not a property of the text a user reads, so no output grader can see it, however sophisticated. Both examples are stdlib-only and run offline.

## CI

[`.github/workflows/checks.yml`](.github/workflows/checks.yml) runs on any change under `infra/`, `examples/`, or `tests/`:

- `terraform fmt -check` across all three trees
- `terraform validate` on each of the seven environment roots, as a matrix so one broken root does not hide the others
- Write-boundary tests for all three trees — stdlib `unittest` reading `.tf` files as text
- Handler logic tests for all three trees
- Deployment package builds for all three trees
- Both example suites — `hermes-agent` and `trace-eval`

Everything runs without cloud credentials, which is deliberate: a check that needs a subscription is a check that gets disabled the first time a secret expires.

The write-boundary tests exist because `terraform validate` accepts every mistake they catch — in each case the wrong value is a valid value in a valid attribute. AWS was originally excluded on the grounds that its boundary is a Lambda resource policy, so getting it wrong fails at plan time. That turned out to be true of the resource policy and only of it: for a caller in the same account Lambda grants invocation if the *identity* policy allows it **or** the resource policy does, and the orchestrator's identity policy is built from a list nothing checked. Widening that list to every tool is a one-word edit that plans, validates, and applies cleanly. The AWS suite guards that half.

## License

Apache License 2.0 — see [LICENSE](LICENSE). The Terraform trees and examples are intended to be copied into your own repositories and adapted.
