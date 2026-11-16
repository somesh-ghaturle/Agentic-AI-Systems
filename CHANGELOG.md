# Changelog

What changed between tagged versions, for someone deciding whether to re-copy a tree or an
example. The detailed record of why each change was made is
[docs/ENHANCEMENT-PLAN.md](docs/ENHANCEMENT-PLAN.md); this file is the short version.

## Unreleased

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

- [docs/NEXT-PHASES-PLAN.md](docs/NEXT-PHASES-PLAN.md), `CLAUDE.md`, `CODEOWNERS`, and a pull
  request template.
- A CI check that the decision-record count in `ROADMAP.md` matches the directory.

### Removed

- `uv.lock`. It was an empty stub that locked nothing.

### Fixed

- `ROADMAP.md` said 5 decision records; there are 4.
- The OWASP link in the README pointed at the web Top Ten rather than the LLM one.

## 0.1.0 — 2026-10-04

First tagged version. Four provider Terraform trees (AWS, Azure, GCP, Snowflake), the opt-in
hybrid POC, 24 runnable examples each with a test suite, the four architecture chapters, the
threat model, and the `trace-eval-service` image published to GHCR.
