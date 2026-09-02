# Repository discrepancies and cleanup candidates

**Audit date:** 2026-09-01
**Scope:** tracked source, documentation, CI configuration, Terraform trees, examples, tests, and
generated working-tree artifacts.

This is a current-state audit, not a cleanup authorization. Items under **Future removal** are
intentionally left in place until their replacement or migration is agreed and verified.

## Resolved discrepancies

| Severity | Finding | Resolution | Recommended action |
| --- | --- | --- | --- |
| Critical | CI is not self-contained for the full test suite. | `tests/requirements.txt` pins FastAPI, OpenTelemetry, and HTTP test dependencies; the main checks workflow installs it before unittest discovery. | Keep the test manifest pinned and update it when dependency-bearing suites change. |
| High | The security-policy test does not include all current examples. | `SECURITY.md` now classifies `edge-agent`, `hermes-dashboard`, and `memory-agent`, and their READMEs carry the required disclaimer. | Keep the policy test as the source-of-truth guard. |
| High | The repository has five Terraform trees, but several documents still describe only three clouds or three trees. | `README.md`, `SECURITY.md`, `.github/workflows/codeql.yml`, `.github/ISSUE_TEMPLATE/security.md`, and `docs/agentic-system-architecture/README.md` now distinguish four cloud/data-platform trees plus the opt-in hybrid POC. | Keep the wording in sync when a new tree or POC is added. |
| High | The infrastructure module catalog contains stale resource names and interfaces. | `infra/MODULES.md` resource entries now match the current Terraform declarations, and the hybrid POC modules are documented. Azure/GCP approval README reconciliation remains a separate follow-up. | Reconcile the remaining Azure/GCP approval README claims against provider schemas. |
| High | Dependency automation omits current dependency manifests. | `.github/workflows/example-deps.yml` now installs and imports `hermes-dashboard` (via `backend/requirements.txt`) and `memory-agent`; `.github/dependabot.yml` now tracks `graph-agent`, `hermes-dashboard/backend`, `memory-agent`, and `services/trace-eval-service`. | Add new dependency-bearing manifests to both files as they appear, or document why one is intentionally excluded. |
| High | Service changes can bypass CI and CodeQL. | `.github/workflows/checks.yml` and `.github/workflows/codeql.yml` now trigger for `services/**` on pushes and pull requests. | Keep service paths in sync when adding new service trees. |
| Low | Status language is not uniform in the enhancement plan. | Task 17 is now `Done`, matching every other completed row; the introduction still documents `Verified` as a distinct, available state for a future task that receives extra verification beyond completion. | Use `Verified` only when a task actually undergoes that extra step. |
| Low | Some broad documentation claims use fixed file counts. | Replaced the fixed Python-file counts in `.pre-commit-config.yaml`, `.github/workflows/checks.yml`, `docs/HARDENING-PLAN.md`, `docs/PRE-COMMIT.md`, `README.md`, and `pyproject.toml` with non-drifting wording ("all Python files" for the lint scope, "most of the Python files" for the `ruff format` reach), so the narrative no longer embeds a count that goes stale as examples and services are added. | Keep counts out of narrative text; re-derive with `git ls-files '*.py' \| wc -l` or `ruff format --check` when a number is actually needed. |
| Medium | The existing `docs/REPO-AUDIT.md` is historical and its scope is stale. | `docs/REPO-AUDIT.md` now carries a historical-document banner at the top that labels its counts (312 files, 8 examples, 3 Terraform trees, 234 tests) as 2026-08-14 snapshots and links this current report. | Keep the banner in sync if the file is updated; treat its counts as historical, not live. |
| Medium | Python support is overstated for the e2e example. | `QUICKSTART.md` now lists `e2e-agent` among the 3.10+ exceptions (and its 3.11 Docker image), and `examples/e2e-agent/README.md` documents the 3.10+ local floor and why (the source uses `str | None` union syntax, a runtime `TypeError` on 3.9). The repository-wide floor stays 3.9 for the zero-dependency examples. | Add a per-example note when an example raises its floor above the repo-wide one. |
| Medium | Deployment guides omit the staging environment. | `infra/terraform-aws/HOW-TO-DEPLOY.md` adds a staging section documenting `envs/staging/` as a release-rehearsal root; `infra/terraform-azure/HOW-TO-DEPLOY.md` and `infra/terraform-gcp/HOW-TO-DEPLOY.md` mark `envs/staging/` as an internal validation-only root (no Azure/GCP handler source exists yet). | Revisit the Azure/GCP staging status when their handler source trees land. |
| Medium | The docs-preview output is easy to mistake for source. | `docs-preview/` is now in the root `.gitignore`; `README.md` documents the local build and cleanup command (`rm -rf docs-preview`); `tests/test_docs_preview.py::test_repo_preview_builds` now writes its output to a temp directory instead of the repo root, fixing the test-hygiene defect that left HTML in the worktree. | Keep `docs-preview/` ignored; do not point the test back at the repo root. |
| Medium | `audit-claims.txt` is an untracked search artifact, not repository source. | `audit-claims.txt` is now in the root `.gitignore`; any stray copy in the worktree was removed. | Regenerate-and-delete it during audits; do not commit. |

## Open discrepancies

None. The follow-up items in the "Future removal or consolidation candidates" section remain
open by design — they are removal decisions, not defects, and wait on the migration conditions
noted there.

## Generated or unnecessary working-tree files

These should not be committed:

- `docs-preview/` — generated static HTML preview.
- `graphify-out/` — generated repository graph output.
- `.pytest_cache/` — pytest cache.
- `.ruff_cache/` — Ruff cache.
- `audit-claims.txt` — temporary audit output.
- Any `__pycache__/` directory or `*.pyc` file.

The root `.gitignore` now covers all of these. None of them are currently committed; `graphify-out/` is no longer present in the worktree, and `.ruff_cache/` may reappear after a local `ruff` run but is ignored. The others may appear during local validation and should be deleted before sharing a clean tree.

The docs-preview test previously wrote to the repository root and did not clean up — a confirmed test-hygiene defect that left stageable HTML in the worktree. `tests/test_docs_preview.py::test_repo_preview_builds` now writes its output to a temp directory, so a full test run no longer stages the preview.

## Future removal or consolidation candidates

| Candidate | Why flag it | Removal condition |
| --- | --- | --- |
| `docs/REPO-AUDIT.md` | Large historical remediation plan overlaps with this current-state report. | Retain only if its historical decisions are still useful; otherwise archive it or merge durable findings into this file. |
| `docs/CONCEPTS-PLAN.md` | Planning document with historical example counts and overlapping roadmap material. | Remove or archive after confirming every still-relevant concept is represented in `ROADMAP.md` or implementation docs. |
| `docs/HARDENING-PLAN.md` | Older hardening plan overlaps with `SECURITY.md`, `THREAT-MODEL.md`, and CI configuration. | Consolidate after checking that no unique control rationale or verification command would be lost. |
| `trace_eval_service/` and `services/trace-eval-service/` | Two service locations may represent overlapping trace-evaluation entry points. **Confirmed:** Both paths exist and contain distinct implementations - root wrapper appears to be a simple entry point while services/ contains the full containerized implementation. | Keep both only while the root wrapper and container service have distinct supported deployment roles; otherwise choose one canonical path. |
| `examples/rag-faiss/` and `examples/rag-langchain/` | Similar RAG examples with different dependency footprints increase maintenance and dependency-scanning cost. | Retain both only if the framework comparison is an explicit supported goal; otherwise designate one canonical example. |
| `examples/hermes-dashboard/requirements.txt` | Duplicates `examples/hermes-dashboard/backend/requirements.txt`, while the compose file and README use the backend manifest. | Remove the root duplicate after CI and local setup instructions use one canonical manifest. |
| Module-level `.terraform.lock.hcl` files | Reusable modules carry lock files in addition to environment-root locks, increasing update and platform-drift maintenance. | Consolidate only after CI proves a shared lock strategy works for all roots and architectures. |

## Verification performed

- Enhancement plan contains 45 numbered tasks.
- Current status rows contain 44 `Done` and 1 `Blocked` task.
- Task 6 (`terraform plan` in CI) remains blocked because enabling it requires a deliberate
  cloud-credential and access-policy decision.
- The full repository unittest suite passes after installing `tests/requirements.txt` (`310 tests,
  21 skipped`). The FastAPI/OpenTelemetry dependency gap and missing security classifications
  identified by the clean-environment audit are now resolved.
- The worktree should be cleaned of generated artifacts before the audit report is committed.
- Current Python file count: 131 tracked files total, 123 in checked directories (examples/, infra/*/src/, tests/, .github/scripts/); the remaining 8 are infra tree tests, the root `trace_eval_service/` wrapper, and `services/trace-eval-service/`.

## Follow-up order

1. ~~Correct the confirmed "three clouds/trees" wording - done~~
2. ~~Remove temporary generated files from local worktrees - done~~
3. Decide whether the historical planning documents remain useful.
4. Decide whether the two trace-eval service paths and the two RAG examples are intentionally
   distinct.
