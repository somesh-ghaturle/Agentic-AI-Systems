# Agentic AI Systems

[![checks](https://github.com/somesh-ghaturle/Agentic-AI-Systems/actions/workflows/checks.yml/badge.svg)](https://github.com/somesh-ghaturle/Agentic-AI-Systems/actions/workflows/checks.yml)
[![example deps](https://github.com/somesh-ghaturle/Agentic-AI-Systems/actions/workflows/example-deps.yml/badge.svg)](https://github.com/somesh-ghaturle/Agentic-AI-Systems/actions/workflows/example-deps.yml)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](QUICKSTART.md)
[![Terraform 1.6+](https://img.shields.io/badge/Terraform-1.6%2B-blue.svg)](QUICKSTART.md)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

Reference implementations of a production agentic architecture: **four provider Terraform
trees** deploying the same system on AWS, Azure, GCP, and Snowflake, an opt-in hybrid POC,
and runnable examples for the architecture and governance patterns behind them. Everything
here is meant to be read, copied into your own repository, and adapted.

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
│   ├── CHOOSING-A-TREE.md        which tree to start from, and what you give up
│   ├── MODULES.md                every module, its dependencies and status
│   ├── policies/                 OPA policies — do the resources agree with each other?
│   ├── terraform-aws/            8 modules · envs/{dev,staging,prod}
│   ├── terraform-azure/          12 modules · envs/{dev,staging,prod,tenant}
│   ├── terraform-snowflake/      10 modules · envs/{dev,staging,prod} · no src/
│   ├── terraform-gcp/            10 modules · envs/{dev,staging,prod}
│   │   ├── README.md             entry point for that cloud
│   │   ├── ARCHITECTURE.md       mermaid diagrams in that cloud's own terms
│   │   ├── HOW-TO-DEPLOY.md      ordered deploy steps and prerequisites
│   │   ├── modules/              approval, orchestration, tools, state, knowledge…
│   │   ├── envs/                 one root per environment
│   │   ├── src/                  handler source + build.sh (run before plan)
│   │   └── tests/                write-boundary tests, stdlib unittest
│   └── terraform-hybrid/         cross-cloud POC · opt-in, disabled by default
├── examples/                     runnable examples and focused proof-of-concepts
│   ├── hermes-agent/             the write boundary in application code
│   ├── trace-eval/               scoring the path rather than the answer
│   ├── eval-red-teaming/         prompt-injection probes against an approval gate
│   ├── approval-gate-fuzzing/    prompt variants that try to bypass approval
│   ├── harness-agent/            continuity across context windows
│   ├── multi-agent-debate/       several agents argue; none of them approves
│   ├── checkpoint-agent/         resuming work after a crash, idempotently
│   ├── e2e-agent/                tracing, audit, provenance over HTTP
│   ├── starter-agent/            the smallest possible agent loop
│   ├── rag-faiss/                build and query a local vector index
│   ├── rag-langchain/            the same, through LangChain
│   ├── langchain-agent/          a minimal LangChain agent
│   ├── context-compaction/       what survives when history is compressed
│   ├── context-overflow/         recency is not the same as relevance
│   ├── graph-agent/              the read/write split as an explicit graph
│   ├── ray-orchestrator/         parallel task execution with Ray
│   ├── memory-agent/             vector, graph, decay, and session memory offline
│   ├── edge-agent/               local SQLite state and file approvals
│   └── hermes-dashboard/         FastAPI/WebSocket approval UX with React
├── docs/
│   ├── agentic-system-architecture/   the six building blocks, as prose
│   ├── agentic-coding-playbook/       working with coding agents day to day
│   ├── REPO-AUDIT.md                  the 2026-08-14 audit and its 22 tasks
│   ├── HARDENING-PLAN.md              CI hardening, 11 tasks over 6 phases
│   ├── CONCEPTS-PLAN.md               adding harness, context, and graph engineering
│   ├── THREAT-MODEL.md                the write boundary from the adversary's side
│   ├── MIGRATION-GUIDE.md             retrofitting these patterns into a project you have
│   ├── FAQ.md                         recurring questions, including the ones commonly answered wrong
│   ├── HOW-TO-RECOVER.md              per-cloud runbook for Terraform state, execution state, stuck claims
│   ├── DECISION-LOGS/                 ADRs — the decisions the code cannot explain itself
│   └── *.md                           governance, security, privacy, runbook, templates
├── tests/                        example suites run by CI
├── CONTRIBUTING.md               what a good example looks like here
├── SECURITY.md                   what counts as a vulnerability here, and how to report it
├── COMPLIANCE.md                 the repo's documented operating controls and evidence model
├── LICENSE                       Apache-2.0
└── .github/
    ├── workflows/checks.yml         fmt, lint, validate, tflint, checkov, boundary tests, builds
    ├── workflows/example-deps.yml   installs each example's pins and imports it
    ├── workflows/codeql.yml         CodeQL over the Python and the workflows, weekly
    ├── scripts/                     linkcheck.py, tfconstraints.py — stdlib-only CI guards
    └── dependabot.yml               monthly pip, actions, and provider updates
```

The per-tree files are shown once under `terraform-gcp/` but exist in all four, except `src/` — the Snowflake tree has none, because its handler logic is SQL. AWS has no `model-integration` module either: its Bedrock guardrail lives in `modules/security`, because a guardrail is a security control on AWS and a separate service on the other three.

## Community and discussion prompts

- **Roadmap**: [ROADMAP.md](ROADMAP.md) — a practical view of the repo's direction, current priorities, and future themes.
- **Discussion starters**: [docs/DISCUSSION-TOPICS.md](docs/DISCUSSION-TOPICS.md) — a ready-to-use set of prompts for GitHub Discussions on architecture, safety, governance, and reuse.
- **Docs preview**: [docs-preview workflow](.github/workflows/docs-preview.yml) — builds a lightweight static HTML review for Markdown changes in pull requests.
- **Citation metadata**: [CITATION.cff](CITATION.cff) — cite the repository in research, teaching, or engineering work.
- **Contribution workflow**: [CONTRIBUTING.md](CONTRIBUTING.md) — what a good example, doc, or patch looks like in this repository.

## System architecture reference

- **Agentic System Architecture**: [docs/agentic-system-architecture/](docs/agentic-system-architecture/README.md) — reference architecture for building agentic systems as production software. Single-agent vs. multi-agent trade-offs, the six building blocks (model routing, tool contracts, memory and state, orchestration, trace-level evals, approval gates), production engineering principles, and a design-review checklist.

## Reference infrastructure

Five Terraform trees under [infra/](infra/) cover the three cloud implementations, Snowflake,
and a cross-cloud topology POC. The provider-specific trees implement the same agentic
architecture on each cloud's own primitives. The [terraform-hybrid](infra/terraform-hybrid/) tree
is an opt-in topology POC and is disabled by default.

| Tree | Orchestrator | Tools | State / approvals | Knowledge |
| --- | --- | --- | --- | --- |
| [terraform-aws/](infra/terraform-aws/) | Step Functions | Lambda | DynamoDB | OpenSearch Serverless |
| [terraform-azure/](infra/terraform-azure/) | Logic Apps | Functions | Storage Tables / Cosmos DB | AI Search |
| [terraform-gcp/](infra/terraform-gcp/) | Cloud Workflows | Cloud Functions gen2 | Firestore | Vertex AI Vector Search |
| [terraform-snowflake/](infra/terraform-snowflake/) | Tasks — *scheduler, not workflow engine* | Stored procedures | Hybrid tables | Cortex Search |
| [terraform-hybrid/](infra/terraform-hybrid/) | AWS Step Functions | GCP Cloud Functions | Azure Cosmos DB | GCP Vertex AI |

Choosing between them: [infra/CHOOSING-A-TREE.md](infra/CHOOSING-A-TREE.md) — the prerequisites that stop an apply before it starts, which boundary survives a later broad grant, and what each tree does not have.

**Snowflake is not a fourth cloud.** It is a data platform running on one of the other three, with no VPC, no cloud IAM, and no general-purpose compute — so its tools are stored procedures and its write boundary is the role graph rather than a policy object. It also has no suspend-and-resume primitive, which makes its approval flow a poll rather than a callback. Pick it when the agent's tools are already queries over data in Snowflake; that trade and its cost are §0 of [CHOOSING-A-TREE.md](infra/CHOOSING-A-TREE.md).

Each tree has its own `ARCHITECTURE.md` with mermaid diagrams drawn in that cloud's terms, a `HOW-TO-DEPLOY.md`, and `envs/dev`, `envs/staging` and `envs/prod` roots. Azure has a fourth root, `envs/tenant`, because the Entra audit alert it applies is tenant-scoped — two roots managing it would revert each other.

`envs/staging` is a release rehearsal rather than a smaller prod: it takes every one of prod's *reversible* controls — private networking, payloads kept out of logs, strict alert thresholds, prod's step budgets — and none of its irreversible ones, so it can be destroyed and rebuilt. Each tree's `envs/staging/main.tf` opens with what it takes from where and why.

**The property they all enforce:** a state-changing action cannot reach production without a human approving that specific action, and that is enforced by the identity platform — not by the prompt, and not by the model choosing to behave. Tools are split into `read` and `write`; only the approval executor can invoke a write tool, and the orchestrator cannot.

**How that boundary is drawn differs by cloud, and each tree's ARCHITECTURE.md section 2 says so plainly rather than claiming parity it does not have:**

- **AWS** — two independent locks: an identity policy and a Lambda resource policy. Remove either and the other still refuses.
- **Azure** — one load-bearing line (`app_role_assignment_required = true`) plus two mitigations. Azure has no resource-policy equivalent for Functions, so this is genuinely thinner, and a CI check and an Entra audit alert guard the line rather than replacing it.
- **GCP** — the closest to the AWS original, because a gen2 function is a Cloud Run service underneath and carries its own IAM policy. It also adds an IAM Deny policy, the only override-proof lock of the three: deny rules evaluate before allow policies, so a later broad grant cannot reopen the path.

**Status.** All thirteen environment roots pass `terraform validate`. The three infrastructure trees have a handler source tree (`src/`) with a build script, so each can `plan` once its packages are built — every function package path is read at plan time to compute a deployment hash, which is why `src/build.sh` runs before `terraform plan` rather than after.

The Snowflake tree has no `src/`: its handler logic is SQL stored procedures defined in `modules/approval`, so there is no package to build and it appears in neither the `handlers` nor the `packages` CI job. The trees are at parity in structure, not in implementation, and the differences are deliberate. Each handler tree is written against its own provider's SDK and its own failure modes: the packaging differs (AWS vendors wheels into the zip because a Lambda zip is the final artifact; Azure and GCP ship source and let Oryx and Cloud Build resolve dependencies), the approval claim differs (a DynamoDB condition expression, a Firestore transaction, a Cosmos ETag), and the trace field names differ because each provider's queries match different ones. `src/tests/` in each tree asserts its own conventions, so a handler copied between trees fails in CI rather than in production.

The model layer is the one place the trees diverge on vendor: AWS calls Claude on Bedrock and GCP calls Claude on Vertex, while Azure calls Azure OpenAI. That is a trade — it buys `azurerm_cognitive_account_rai_policy`, the only Azure content filter that is a first-class Terraform resource and the closest analogue to a Bedrock guardrail, at the cost of model consistency. Serving Claude through the Azure AI model catalog instead would reverse both halves of that trade.

## Runnable examples

**Worked examples** — tests, architecture notes, and no dependencies:

- [hermes-agent](examples/hermes-agent/README.md) — routing and the write boundary in application code
- [trace-eval](examples/trace-eval/README.md) — trace-level evaluation, scoring the path rather than the answer
- [harness-agent](examples/harness-agent/README.md) — continuity across context windows, and the four things a harness refuses to let an agent do
- [multi-agent-debate](examples/multi-agent-debate/README.md) — several agents argue a proposal into better shape, and why none of them is allowed to approve it

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
- [tool-discovery](examples/tool-discovery/README.md) — tools loaded from a directory at runtime, and why the read/write split has to survive being discovered rather than declared
- [memory-agent](examples/memory-agent/README.md) — offline vector, graph, decay, and session memory patterns
- [edge-agent](examples/edge-agent/README.md) — local SQLite state and file-based approvals for devices
- [hermes-dashboard](examples/hermes-dashboard/README.md) — React/FastAPI human approval workflow UX

**Hermes** is the runnable counterpart to the infrastructure above. It routes a request to a handler, runs read tools on the spot, and returns anything that would change state as a proposal that stops until a human approves *that specific action* — approval bound to a fingerprint of the exact arguments, single-use, expiring. The router holds no reference to a write tool; the approval executor holds nothing else. Standard library only, no model, no cloud account, and the boundary tests were mutation-tested rather than trusted.

**trace-eval** is the feedback edge from the architecture diagram, running. It scores the same runs two ways — one grader reads the final answer, one reads the trace — and prints where they disagree. Against an agent with no write boundary, it finds three requests where the answer was on topic, helpful, and graded PASS while a production service was restarted with nobody's authorisation. Whether a human approved an action is not a property of the text a user reads, so no output grader can see it, however sophisticated. Both examples are stdlib-only and run offline.

## Working with coding agents

- **Agentic Coding Playbook**: [docs/agentic-coding-playbook/](docs/agentic-coding-playbook/README.md) — a drop-in kit for treating Claude (or any coding agent) as an agent inside your workflow rather than a chatbot you consult. Eight habits, a two-week ramp, named antipatterns, a team workflow for shared repos, enterprise rollout and agent-security guidance, and copy-paste templates for `CLAUDE.md`, scoped rules, slash commands, skills, and subagents.

## Templates & checklists

Review gates, to run before a system ships rather than after it misbehaves:

- Governance checklist: [docs/governance-checklist.md](docs/governance-checklist.md)
- Security checklist: [docs/security-checklist.md](docs/security-checklist.md)
- Privacy checklist: [docs/privacy-checklist.md](docs/privacy-checklist.md)

What in the four trees is credential material and how each piece rotates — which is a shorter list than it sounds, because the Terraform provisions no long-lived credentials at all: [docs/SECRETS-ROTATION.md](docs/SECRETS-ROTATION.md). It names the three places a value still passes through something that retains it, and why the Snowflake tree federates rather than holding a key.

Questions that come up more than once, answered against what the code does rather than what it is assumed to do: [docs/FAQ.md](docs/FAQ.md). Three of its answers correct a belief the repository itself used to print — there is no switch that disables the approval gate, nothing expires a claim after 24 hours, and a model cannot call a write tool because it is never handed one.

Retrofitting these patterns into an agent that already works, in the order that pays off soonest: [docs/MIGRATION-GUIDE.md](docs/MIGRATION-GUIDE.md). The write boundary first, because an ungated write path is a present risk while a missing eval harness is a future one. Its pitfalls section is specific to this repository — every entry is a mistake that was made here, with the artefact still in the tree to look at.

The adversary's view of the write boundary — what a compromised orchestrator reaches, what a prompt-injected model reaches, what a leaked approval claim buys, and which of the four trees survives each: [docs/THREAT-MODEL.md](docs/THREAT-MODEL.md). It is explicit about what is *not* defended, which is the more useful half — and the row where the trees genuinely differ is a later broad grant, which GCP's deny policy survives, AWS and Azure do not, and Snowflake loses transitively.

What to actually run when Terraform's own state is locked or gone, an execution-state row is corrupted, or an approval claim is stuck: [docs/HOW-TO-RECOVER.md](docs/HOW-TO-RECOVER.md). All four trees apply against a local, unbacked-up state file today, and Azure's execution-state table turns out to have no recovery path configured at all — the soft-delete setting on that storage account protects blobs, not the Table Storage resource state actually lives in.

Documents to fill in per system, and one to reach for when it breaks:

- Model card template: [docs/model-card-template.md](docs/model-card-template.md)
- Dataset datasheet template: [docs/datasheet-template.md](docs/datasheet-template.md)
- Incident runbook: [docs/incident-runbook.md](docs/incident-runbook.md)

The decisions the code cannot explain about itself — why the AWS write boundary needs a static test on top of its resource policy, why Azure calls Azure OpenAI while the other two trees call Claude, why GCP runs two Firestore databases instead of one Spanner instance, and why half the examples import nothing: [docs/DECISION-LOGS/](docs/DECISION-LOGS/README.md). Each record names the alternative that lost and the observable change that would reopen it.

Also here: the repository audit of 2026-08-14 and its remediation plan, [docs/REPO-AUDIT.md](docs/REPO-AUDIT.md), and the [CONTRIBUTING guidelines](CONTRIBUTING.md).

## CI

[`.github/workflows/checks.yml`](.github/workflows/checks.yml) runs on any change under `infra/`, `examples/`, `tests/`, `docs/`, the root markdown files, `pyproject.toml`, or the workflow's own scripts — twelve jobs, checking:

- `terraform fmt -check` across all four trees, plus a provider-pin check that `terraform validate` cannot see
- `ruff check` over all 86 Python files, against the rules in `pyproject.toml` — the same command and the same verdict a contributor gets locally
- `terraform validate` on each of the ten environment roots, as a matrix so one broken root does not hide the others
- `tflint` over all thirty modules and ten roots — `validate` only ever sees a module through a root that calls it, which is why nothing reported that twelve Azure modules pinned no provider version
- `checkov` over the trees, failing on any finding not skipped by name and with a reason in [`.checkov.yaml`](.checkov.yaml)
- `conftest` over all four trees against the OPA policies in [`infra/policies/`](infra/policies/README.md), which check whether resources agree with each other — a content filter that nothing references is the case they exist for — plus the policies' own unit tests
- Write-boundary tests for all four trees — stdlib `unittest` reading `.tf` files as text
- Handler logic tests for the three trees that have handlers
- Deployment package builds for the three trees that have packages
- The example suites under `tests/` — nine of the twelve examples, via `unittest discover`; `langchain-agent`, `rag-langchain`, and `ray-orchestrator` have none
- A syntax check over all twelve examples, including those three
- A relative-link check over every markdown file, external URLs deliberately excluded
- A gitleaks scan over the full git history rather than the tip commit, because a credential committed and later deleted is the case history scanning exists to catch

Documentation used to run no checks at all. This repository is mostly markdown by volume and by purpose, and a documentation-only commit merged green until the path filters were widened to cover it — the miss that found was two links to a workflow that had been renamed.

[`.github/workflows/example-deps.yml`](.github/workflows/example-deps.yml) runs only on changes under `examples/` or `tests/`. It installs each example's pinned `requirements.txt` and imports its entry modules — the six examples that carry dependencies, one matrix leg each. It has its own file because it has its own trigger: it downloads Torch, Ray, and FAISS, and has no business running when someone edits a Terraform module.

That job exists because of a failure this repository actually had. Two LangChain examples imported an API the pinned version had already deleted, and CI stayed green — the suites did not cover those examples, and a syntax check parses rather than imports, so it happily accepts a module naming a package that no longer exists. A stale pin is invisible to every check that does not install the pin. [`.github/dependabot.yml`](.github/dependabot.yml) covers the other half: the syntax and import checks catch a pin that is *broken*, Dependabot catches one that is merely *old*.

Everything runs without cloud credentials, which is deliberate: a check that needs a subscription is a check that gets disabled the first time a secret expires. The import job needs PyPI and nothing else — no model key, because importing a module builds no client.

The write-boundary tests exist because `terraform validate` accepts every mistake they catch — in each case the wrong value is a valid value in a valid attribute. AWS was originally excluded on the grounds that its boundary is a Lambda resource policy, so getting it wrong fails at plan time. That turned out to be true of the resource policy and only of it: for a caller in the same account Lambda grants invocation if the *identity* policy allows it **or** the resource policy does, and the orchestrator's identity policy is built from a list nothing checked. Widening that list to every tool is a one-word edit that plans, validates, and applies cleanly. The AWS suite guards that half.

## Contributing

Runnable examples, post-mortems, and additional references are welcome via pull request. See [CONTRIBUTING.md](CONTRIBUTING.md) — the short version is that examples should be reproducible and their dependencies pinned.

## Security

If you believe the write boundary can be bypassed — in any of the three Terraform trees or in the two boundary examples — please report it privately rather than opening an issue. Everything here is designed to be copied, so a public report is a working recipe against every copy already in the wild. See [SECURITY.md](SECURITY.md) for what is in scope and how to report.

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
