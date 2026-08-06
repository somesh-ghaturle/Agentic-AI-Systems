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

- LangChain (practical agent and orchestration patterns): https://github.com/langchain-ai/langchain
- Ray (distributed execution for agents and workloads): https://github.com/ray-project/ray
- Kubeflow (ML orchestration and pipelines): https://www.kubeflow.org/
- MLflow (experiment tracking and reproducibility): https://mlflow.org/
- Google MLOps: Continuous Delivery for Machine Learning (guide): https://cloud.google.com/architecture/mlops-continuous-delivery-automation
- Model Cards for model reporting (best practices for model documentation): https://modelcards.withgoogle.com/
- Hidden Technical Debt in Machine Learning Systems (operational risks paper): https://papers.nips.cc/paper/5656-hidden-technical-debt-in-machine-learning-systems.pdf

If you'd like, I can add more targeted advanced references (papers, repos, templates) for governance, security, or large-scale orchestration — tell me which areas to prioritize.

## Governance & security references

- NIST AI Risk Management Framework: https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf
- EU AI Act (summary and compliance guidance): https://commission.europa.eu/publications/eu-artificial-intelligence-act_en
- Responsible AI practices (Microsoft): https://learn.microsoft.com/en-us/azure/ai/fundamentals/responsible-ai
- Model Cards & documentation best practices: https://modelcards.withgoogle.com/
- OWASP AI Security Top Ten (emerging guidance): https://owasp.org/www-project-top-ten/

These resources provide governance, risk, and security perspectives suitable for enterprise adoption.

## Working with coding agents

- **Agentic AI Arch End-to-End**: [docs/agentic-ai-arch-end-to-end/](docs/agentic-ai-arch-end-to-end/README.md) — a drop-in kit for treating Claude (or any coding agent) as an agent inside your workflow rather than a chatbot you consult. Eight habits, a two-week ramp, named antipatterns, and copy-paste templates for `CLAUDE.md`, scoped rules, slash commands, skills, and subagents.

## Included templates & checklists

- Governance checklist: [docs/governance-checklist.md](docs/governance-checklist.md)
- Security checklist: [docs/security-checklist.md](docs/security-checklist.md)
- Privacy checklist: [docs/privacy-checklist.md](docs/privacy-checklist.md)
- Starter agent example: [examples/starter-agent/README.md](examples/starter-agent/README.md)
- CONTRIBUTING guidelines: [CONTRIBUTING.md](CONTRIBUTING.md)

More runnable templates (examples):

- LangChain agent: [examples/langchain-agent/README.md](examples/langchain-agent/README.md)
- Retrieval (RAG) with FAISS: [examples/rag-faiss/README.md](examples/rag-faiss/README.md)
- Ray orchestration sample: [examples/ray-orchestrator/README.md](examples/ray-orchestrator/README.md)
 - End-to-end secure & observable agent (traceability, SLA, governance): [examples/e2e-agent/README.md](examples/e2e-agent/README.md)

CI: A basic smoke-test workflow is included at `.github/workflows/smoke.yml` to run tests and basic checks on push/PR.