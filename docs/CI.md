# CI

What runs on a pull request, and why each check exists. This used to be a section of the root
README; it moved here so that file can stay short. The counts below are still checked against
the tree by [`docs_counts.py`](../.github/scripts/docs_counts.py).

[`.github/workflows/checks.yml`](../.github/workflows/checks.yml) runs on any change under `infra/`, `examples/`, `tests/`, `docs/`, the root markdown files, `pyproject.toml`, or the workflow's own scripts — fourteen jobs, checking:

- `terraform fmt -check` across all four trees, plus a provider-pin check that `terraform validate` cannot see
- `ruff check` over all Python files, against the rules in `pyproject.toml` — the same command and the same verdict a contributor gets locally, plus a guard that Mermaid diagrams stay fenced in Markdown rather than in `.mmd` files
- A Terraform cost estimate over `infra/` that fails above a monthly threshold
- `terraform validate` on each of the sixteen roots — the thirteen environment roots and the three remote-state bootstraps — as a matrix so one broken root does not hide the others
- `tflint` over all forty-five modules and fourteen roots, plus the three bootstraps — `validate` only ever sees a module through a root that calls it, which is why nothing reported that twelve Azure modules pinned no provider version
- `checkov` over the trees, failing on any finding not skipped by name and with a reason in [`.checkov.yaml`](../.checkov.yaml)
- `conftest` over all four trees against the OPA policies in [`infra/policies/`](../infra/policies/README.md), which check whether resources agree with each other — a content filter that nothing references is the case they exist for — plus the policies' own unit tests
- Write-boundary tests for all four trees — stdlib `unittest` reading `.tf` files as text
- Handler logic tests for the three trees that have handlers
- Deployment package builds for the three trees that have packages
- The example suites under `tests/` — twenty-four of the twenty-four examples, via `unittest discover`. Suites whose tests need an example's package skip here, and `example-deps.yml` runs them against that example's pins
- A syntax check over all twenty-four examples
- A relative-link check over every markdown file, external URLs deliberately excluded
- A check that the counts the documentation states match the counts the tree has, because a stale number in prose is invisible until someone acts on it
- A check that each architecture chapter and its runnable counterpart point at each other
- A gitleaks scan over the full git history rather than the tip commit, because a credential committed and later deleted is the case history scanning exists to catch

Documentation used to run no checks at all. This repository is mostly markdown by volume and by purpose, and a documentation-only commit merged green until the path filters were widened to cover it — the miss that found was two links to a workflow that had been renamed.

[`.github/workflows/example-deps.yml`](../.github/workflows/example-deps.yml) runs only on changes under `examples/`, `tests/`, or the service's own directories. It installs each example's pinned `requirements.txt` and imports its entry modules — the eight that carry dependencies, one matrix leg each. It has its own file because it has its own trigger: it downloads Torch, Ray, and FAISS, and has no business running when someone edits a Terraform module.

That job exists because of a failure this repository actually had. Two LangChain examples imported an API the pinned version had already deleted, and CI stayed green — the suites did not cover those examples, and a syntax check parses rather than imports, so it happily accepts a module naming a package that no longer exists. A stale pin is invisible to every check that does not install the pin. [`.github/dependabot.yml`](../.github/dependabot.yml) covers the other half: the syntax and import checks catch a pin that is *broken*, Dependabot catches one that is merely *old*.

The same workflow builds every Dockerfile in the tree and asserts each image does not run as root. It was added after the `rag-langchain` image stopped building without anything noticing: the import job installs each example's pins on this workflow's Python, the image installs them on the Python its Dockerfile names, and the two had drifted apart.

Everything runs without cloud credentials, which is deliberate: a check that needs a subscription is a check that gets disabled the first time a secret expires. The import job needs PyPI and nothing else — no model key, because importing a module builds no client.

## The one required check

[`.github/workflows/gate.yml`](../.github/workflows/gate.yml) is the only check the `main` ruleset requires. The workflows above have path filters, and a required check that never starts leaves a pull request waiting forever, so their jobs cannot be required by name. `gate` has no filter: it runs on every pull request, waits for whatever else started on the same commit, and fails if any of it failed. Requiring that one job requires all the others exactly when they apply.

## What is not a check

Three workflows never gate a pull request:

- [`pages.yml`](../.github/workflows/pages.yml) publishes the interactive diagrams to GitHub Pages when they change on `main`.
- [`external-links.yml`](../.github/workflows/external-links.yml) reports dead external links weekly, as an issue.
- [`plan.yml`](../.github/workflows/plan.yml) runs `terraform plan` on one AWS root, by hand, through OIDC with a read-only role. It is the only workflow that can reach a cloud account, it does nothing until one is configured, and [ADR 0005](DECISION-LOGS/0005-opt-in-plan-with-oidc.md) records why it exists.

The write-boundary tests exist because `terraform validate` accepts every mistake they catch — in each case the wrong value is a valid value in a valid attribute. AWS was originally excluded on the grounds that its boundary is a Lambda resource policy, so getting it wrong fails at plan time. That turned out to be true of the resource policy and only of it: for a caller in the same account Lambda grants invocation if the *identity* policy allows it **or** the resource policy does, and the orchestrator's identity policy is built from a list nothing checked. Widening that list to every tool is a one-word edit that plans, validates, and applies cleanly. The AWS suite guards that half.
