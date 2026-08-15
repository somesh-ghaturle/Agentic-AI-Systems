# Agentic AI Systems

[![checks](https://github.com/somesh-ghaturle/Agentic-AI-Systems/actions/workflows/checks.yml/badge.svg)](https://github.com/somesh-ghaturle/Agentic-AI-Systems/actions/workflows/checks.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

Reference implementations of a production agentic architecture: **three parallel Terraform trees** deploying the same system on AWS, Azure, and GCP, **eleven runnable examples**, and the architecture and governance documents behind them. Everything here is meant to be read, copied into your own repository, and adapted.

The property the whole repository is organised around: **a state-changing action cannot reach production without a human approving that specific action** — enforced by the identity platform, not by the prompt and not by the model choosing to behave.

## Run something in 30 seconds

No model, no cloud account, no network, no dependencies — Python 3.9+ and the standard library.

```bash
git clone https://github.com/somesh-ghaturle/Agentic-AI-Systems.git
cd Agentic-AI-Systems

# Ask an agent to change something. It stops at the write boundary.
python3 examples/hermes-agent/agent.py "restart the billing service"
```

```text
trace   60d7c93b22af4c2aa0840367030695f3
intent  act → act()
status  awaiting approval
write   restart_service(service='billing')
why     Service 'billing' reports healthy=True; a restart clears the connection pool and takes about 40 seconds.
digest  9ef8f9b497df3e68…
next    re-run with --approve to authorise exactly this action
```

Re-run with `--approve` to authorise that exact call, then see why output-only evaluation cannot catch a missing approval:

```bash
python3 examples/trace-eval/eval.py
```

It scores the same runs twice — one grader reads the final answer, one reads the trace — and prints the three requests where the answer was on topic, helpful, and graded PASS while a production service was restarted with nobody's authorisation.

## Repository layout

```text
Agentic-AI-Systems/
├── infra/                        three Terraform trees, same architecture per cloud
│   ├── terraform-aws/            8 modules · envs/{dev,prod}
│   ├── terraform-azure/          12 modules · envs/{dev,prod,tenant}
│   └── terraform-gcp/            10 modules · envs/{dev,prod}
│       ├── README.md             entry point for that cloud
│       ├── ARCHITECTURE.md       mermaid diagrams in that cloud's own terms
│       ├── HOW-TO-DEPLOY.md      ordered deploy steps and prerequisites
│       ├── modules/              approval, orchestration, tools, state, knowledge…
│       ├── envs/                 one root per environment
│       ├── src/                  handler source + build.sh (run before plan)
│       └── tests/                write-boundary tests, stdlib unittest
├── examples/                     eleven runnable examples, worked → minimal
│   ├── hermes-agent/             the write boundary in application code
│   ├── trace-eval/               scoring the path rather than the answer
│   ├── harness-agent/            continuity across context windows
│   ├── e2e-agent/                tracing, audit, provenance over HTTP
│   ├── starter-agent/            the smallest possible agent loop
│   ├── rag-faiss/                build and query a local vector index
│   ├── rag-langchain/            the same, through LangChain
│   ├── langchain-agent/          a minimal LangChain agent
│   ├── context-compaction/       what survives when history is compressed
│   ├── graph-agent/              the read/write split as an explicit graph
│   └── ray-orchestrator/         parallel task execution with Ray
├── docs/
│   ├── agentic-system-architecture/   the six building blocks, as prose
│   ├── agentic-coding-playbook/       working with coding agents day to day
│   ├── REPO-AUDIT.md                  the 2026-08-14 audit and its 16 fixes
│   ├── HARDENING-PLAN.md              CI hardening, 11 tasks over 6 phases
│   ├── CONCEPTS-PLAN.md               adding harness, context, and graph engineering
│   └── *.md                           governance, security, privacy, runbook, templates
├── tests/                        example suites run by CI
├── CONTRIBUTING.md               what a good example looks like here
├── LICENSE                       Apache-2.0
└── .github/
    ├── workflows/checks.yml         fmt, validate, boundary tests, handlers, builds
    ├── workflows/example-deps.yml   installs each example's pins and imports it
    └── dependabot.yml               monthly pip, actions, and provider updates
```

The per-tree files are shown once under `terraform-gcp/` but exist in all three. AWS has no `model-integration` module — its Bedrock guardrail lives in `modules/security`, because a guardrail is a security control on AWS and a separate service on the other two.

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

## Runnable examples

**Worked examples** — tests, architecture notes, and no dependencies:

- [hermes-agent](examples/hermes-agent/README.md) — routing and the write boundary in application code
- [trace-eval](examples/trace-eval/README.md) — trace-level evaluation, scoring the path rather than the answer
- [harness-agent](examples/harness-agent/README.md) — continuity across context windows, and the four things a harness refuses to let an agent do

**Applied example** — tracing, audit, provenance, and governance docs over HTTP:

- [e2e-agent](examples/e2e-agent/README.md)

**Minimal references** — short scripts showing one idea each:

- [starter-agent](examples/starter-agent/README.md) — the smallest possible agent loop
- [rag-faiss](examples/rag-faiss/README.md) — build and query a local vector index
- [rag-langchain](examples/rag-langchain/README.md) — the same, through LangChain
- [langchain-agent](examples/langchain-agent/README.md) — a minimal LangChain agent
- [ray-orchestrator](examples/ray-orchestrator/README.md) — parallel task execution with Ray
- [context-compaction](examples/context-compaction/README.md) — what survives when history is compressed, and why truncation drops the wrong things
- [graph-agent](examples/graph-agent/README.md) — the same read/write split as hermes-agent, as an explicit LangGraph graph

**Hermes** is the runnable counterpart to the infrastructure above. It routes a request to a handler, runs read tools on the spot, and returns anything that would change state as a proposal that stops until a human approves *that specific action* — approval bound to a fingerprint of the exact arguments, single-use, expiring. The router holds no reference to a write tool; the approval executor holds nothing else. Standard library only, no model, no cloud account, and the boundary tests were mutation-tested rather than trusted.

**trace-eval** is the feedback edge from the architecture diagram, running. It scores the same runs two ways — one grader reads the final answer, one reads the trace — and prints where they disagree. Against an agent with no write boundary, it finds three requests where the answer was on topic, helpful, and graded PASS while a production service was restarted with nobody's authorisation. Whether a human approved an action is not a property of the text a user reads, so no output grader can see it, however sophisticated. Both examples are stdlib-only and run offline.

## Working with coding agents

- **Agentic Coding Playbook**: [docs/agentic-coding-playbook/](docs/agentic-coding-playbook/README.md) — a drop-in kit for treating Claude (or any coding agent) as an agent inside your workflow rather than a chatbot you consult. Eight habits, a two-week ramp, named antipatterns, a team workflow for shared repos, enterprise rollout and agent-security guidance, and copy-paste templates for `CLAUDE.md`, scoped rules, slash commands, skills, and subagents.

## Templates & checklists

Review gates, to run before a system ships rather than after it misbehaves:

- Governance checklist: [docs/governance-checklist.md](docs/governance-checklist.md)
- Security checklist: [docs/security-checklist.md](docs/security-checklist.md)
- Privacy checklist: [docs/privacy-checklist.md](docs/privacy-checklist.md)

Documents to fill in per system, and one to reach for when it breaks:

- Model card template: [docs/model-card-template.md](docs/model-card-template.md)
- Dataset datasheet template: [docs/datasheet-template.md](docs/datasheet-template.md)
- Incident runbook: [docs/incident-runbook.md](docs/incident-runbook.md)

Also here: the repository audit of 2026-08-14 and its remediation plan, [docs/REPO-AUDIT.md](docs/REPO-AUDIT.md), and the [CONTRIBUTING guidelines](CONTRIBUTING.md).

## CI

[`.github/workflows/checks.yml`](.github/workflows/checks.yml) runs on any change under `infra/`, `examples/`, or `tests/`:

- `terraform fmt -check` across all three trees
- `terraform validate` on each of the seven environment roots, as a matrix so one broken root does not hide the others
- Write-boundary tests for all three trees — stdlib `unittest` reading `.tf` files as text
- Handler logic tests for all three trees
- Deployment package builds for all three trees
- The example suites under `tests/` — `hermes-agent`, `trace-eval`, and the `starter-agent` smoke tests, via `unittest discover`
- A syntax check over all eleven examples, including those with no suite of their own

[`.github/workflows/example-deps.yml`](.github/workflows/example-deps.yml) runs only on changes under `examples/` or `tests/`. It installs each example's pinned `requirements.txt` and imports its entry modules — the five examples that carry dependencies, one matrix leg each. It has its own file because it has its own trigger: it downloads Torch, Ray, and FAISS, and has no business running when someone edits a Terraform module.

That job exists because of a failure this repository actually had. Two LangChain examples imported an API the pinned version had already deleted, and CI stayed green — the suites did not cover those examples, and a syntax check parses rather than imports, so it happily accepts a module naming a package that no longer exists. A stale pin is invisible to every check that does not install the pin. [`.github/dependabot.yml`](.github/dependabot.yml) covers the other half: the syntax and import checks catch a pin that is *broken*, Dependabot catches one that is merely *old*.

Everything runs without cloud credentials, which is deliberate: a check that needs a subscription is a check that gets disabled the first time a secret expires. The import job needs PyPI and nothing else — no model key, because importing a module builds no client.

The write-boundary tests exist because `terraform validate` accepts every mistake they catch — in each case the wrong value is a valid value in a valid attribute. AWS was originally excluded on the grounds that its boundary is a Lambda resource policy, so getting it wrong fails at plan time. That turned out to be true of the resource policy and only of it: for a caller in the same account Lambda grants invocation if the *identity* policy allows it **or** the resource policy does, and the orchestrator's identity policy is built from a list nothing checked. Widening that list to every tool is a one-word edit that plans, validates, and applies cleanly. The AWS suite guards that half.

## Contributing

Runnable examples, post-mortems, and additional references are welcome via pull request. See [CONTRIBUTING.md](CONTRIBUTING.md) — the short version is that examples should be reproducible and their dependencies pinned.

## Further reading

**Architecture and patterns**

- [alirezadir/Agentic-AI-Systems](https://github.com/alirezadir/Agentic-AI-Systems) — practical system design examples, tutorials, and architecture documentation.
- [all-agentic-architectures (FareedKhan-dev)](https://github.com/FareedKhan-dev/all-agentic-architectures) — production-grade architecture library and runnable examples.
- [Voyager architecture notebook](https://github.com/FareedKhan-dev/all-agentic-architectures/blob/main/docs/architectures/29_voyager.ipynb) — concrete architecture walkthrough example.
- [agentic-ai-architecture topic on GitHub](https://github.com/topics/agentic-ai-architecture) — broad architecture-focused repositories and references.
- [agentic-ai topic on GitHub](https://github.com/topics/agentic-ai) — ecosystem-wide discovery of agentic AI projects.

**Orchestration and operations**

- [LangChain](https://github.com/langchain-ai/langchain) — practical agent and orchestration patterns.
- [Ray](https://github.com/ray-project/ray) — distributed execution for agents and workloads.
- [Kubeflow](https://www.kubeflow.org/) — ML orchestration and pipelines.
- [MLflow](https://mlflow.org/) — experiment tracking and reproducibility.
- [Google MLOps: Continuous Delivery for Machine Learning](https://cloud.google.com/architecture/mlops-continuous-delivery-automation) — the reference guide.
- [Hidden Technical Debt in Machine Learning Systems](https://papers.nips.cc/paper/5656-hidden-technical-debt-in-machine-learning-systems.pdf) — the operational-risk paper worth reading first.

**Governance, risk, and security**

- [NIST AI Risk Management Framework](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf)
- [EU AI Act](https://commission.europa.eu/publications/eu-artificial-intelligence-act_en) — summary and compliance guidance.
- [Responsible AI practices](https://learn.microsoft.com/en-us/azure/ai/fundamentals/responsible-ai) — Microsoft.
- [OWASP AI Security Top Ten](https://owasp.org/www-project-top-ten/) — emerging guidance.
- [Model Cards](https://modelcards.withgoogle.com/) — best practices for model documentation and reporting.

## License

Apache License 2.0 — see [LICENSE](LICENSE). The Terraform trees and examples are intended to be copied into your own repositories and adapted.
