# Changelog

What changed between tagged versions, for someone deciding whether to re-copy a tree or an
example. The detailed record of why each change was made is
[docs/ENHANCEMENT-PLAN.md](docs/ENHANCEMENT-PLAN.md) and
[docs/NEXT-PHASES-PLAN.md](docs/NEXT-PHASES-PLAN.md); this file is the short version.

## Unreleased

Phase 2 of [docs/NEXT-PHASES-PLAN.md](docs/NEXT-PHASES-PLAN.md). Nothing here was planned or
applied against a real cloud account; it passes the same static checks as the rest of the trees.

### Changed — read before re-copying the Azure tree

- **Azure execution state is a Cosmos DB container, not a Storage Table.** The old table had
  no recovery path; the new account has continuous backup in prod and account keys switched
  off. Applying this over an existing environment replaces the table. The tool variables
  `STATE_STORAGE_ACCOUNT` and `STATE_TABLE_NAME` are now `STATE_COSMOS_ENDPOINT`,
  `STATE_DATABASE` and `STATE_CONTAINER`.
- **The Azure default model is `gpt-5.1` `2025-11-13`**, up from `gpt-4o` `2024-11-20`, which
  Microsoft retires on 2027-04-14. See the amendment to ADR 0002.
- The Azure `terraform.tfvars.example` files no longer set `MODEL_DEPLOYMENT` on the `reason`
  tool. That value overrode the deployment name the root wires and pointed at a deployment
  that does not exist.
- The AWS backend sketches use `use_lockfile` where they used `dynamodb_table`.
- Every Dockerfile pins its base image by digest.

### Added

- `bootstrap/` roots for AWS, Azure and GCP that create the remote-state bucket and print the
  backend block for it.
- GitHub Pages site for the interactive diagrams, and a link to the live viewer under every
  embedded GIF.
- `gate.yml`, the one check `main` requires; a CI job that builds every image; and `plan.yml`,
  a hand-run `terraform plan` through OIDC that is never a check
  ([ADR 0005](docs/DECISION-LOGS/0005-opt-in-plan-with-oidc.md)).

## 0.2.0 — 2026-11-16

### Fixed

- The `rag-langchain` image did not build: its base image was Python 3.11 and the pinned
  `numpy` needs 3.12. It now uses 3.12.
- `ROADMAP.md` said 5 decision records; there are 4.
- Three README links: the OWASP link pointed at the web Top Ten rather than the LLM one, and
  the Google MLOps and Microsoft Responsible AI links were dead.

### Changed

- The `trace-eval-service` image, and the `rag-langchain` and `starter-agent` example images,
  run as a non-root user.
- The published image carries an SBOM and a build provenance attestation.
- Dependabot now watches the Terraform providers in the Azure modules, the Snowflake tree and
  the hybrid POC, the two npm manifests, and `tests/requirements.txt`.
- The README's CI section moved to [docs/CI.md](docs/CI.md).
- The 3.9 floor job is pinned to `ubuntu-24.04`, the last runner image with a Python 3.9 build.
- Example, service and GitHub Actions pins bumped by Dependabot (2026-11-01).
- The README architecture diagrams were re-rendered.

### Added

- A weekly report of dead external links, opened as an issue and never a gate.
- [docs/NEXT-PHASES-PLAN.md](docs/NEXT-PHASES-PLAN.md), `CLAUDE.md`, `CODEOWNERS`, and a pull
  request template.
- A CI check that the decision-record count in `ROADMAP.md` matches the directory.

### Removed

- `uv.lock`. It was an empty stub that locked nothing.

## 0.1.0 — 2026-10-04

First tagged version. Four provider Terraform trees (AWS, Azure, GCP, Snowflake), the opt-in
hybrid POC, 24 runnable examples each with a test suite, the four architecture chapters, the
threat model, and the `trace-eval-service` image published to GHCR.
