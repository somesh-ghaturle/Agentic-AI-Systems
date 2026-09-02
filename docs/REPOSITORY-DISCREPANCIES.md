# Repository discrepancies and cleanup candidates

**Audit date:** 2026-09-01
**Scope:** tracked source, documentation, CI configuration, Terraform trees, examples, tests, and
generated working-tree artifacts.

This is a current-state audit. All discrepancies and consolidation candidates below have been
resolved. The "Consolidation decisions" section records what was kept, what was removed, and why.

## Resolved discrepancies

| Severity | Finding | Resolution | Recommended action |
| --- | --- | --- | --- |
| Critical | CI is not self-contained for the full test suite. | `tests/requirements.txt` pins FastAPI, OpenTelemetry, and HTTP test dependencies; the main checks workflow installs it before unittest discovery. | Keep the test manifest pinned and update it when dependency-bearing suites change. |
| High | The security-policy test does not include all current examples. | `SECURITY.md` now classifies `edge-agent`, `hermes-dashboard`, and `memory-agent`, and their READMEs carry the required disclaimer. | Keep the policy test as the source-of-truth guard. |
| High | The repository has five Terraform trees, but several documents still describe only three clouds or three trees. | `README.md`, `SECURITY.md`, `.github/workflows/codeql.yml`, `.github/ISSUE_TEMPLATE/security.md`, and `docs/agentic-system-architecture/README.md` now distinguish four cloud/data-platform trees plus the opt-in hybrid POC. | Keep the wording in sync when a new tree or POC is added. |
| High | The infrastructure module catalog contains stale resource names and interfaces. | `infra/MODULES.md` resource entries now match the current Terraform declarations, and the hybrid POC modules are documented. Azure/GCP approval README resource names have been reconciled: Azure now lists `azurerm_linux_function_app.approval`, `azurerm_servicebus_topic.approval`, `azurerm_cosmosdb_account.approvals`, and the `azuread_application` pair; GCP now lists `google_cloudfunctions2_function` (the v2 API, not the retired v1 `google_cloudfunctions_function`). | Keep the README components list in sync when a resource is renamed or replaced. |
| High | Dependency automation omits current dependency manifests. | `.github/workflows/example-deps.yml` now installs and imports `hermes-dashboard` (via `backend/requirements.txt`) and `memory-agent`; `.github/dependabot.yml` now tracks `graph-agent`, `hermes-dashboard/backend`, `memory-agent`, and `services/trace-eval-service`. | Add new dependency-bearing manifests to both files as they appear, or document why one is intentionally excluded. |
| High | Service changes can bypass CI and CodeQL. | `.github/workflows/checks.yml` and `.github/workflows/codeql.yml` now trigger for `services/**` on pushes and pull requests. | Keep service paths in sync when adding new service trees. |
| Low | Status language is not uniform in the enhancement plan. | Task 17 is now `Done`, matching every other completed row; the introduction still documents `Verified` as a distinct, available state for a future task that receives extra verification beyond completion. | Use `Verified` only when a task actually undergoes that extra step. |
| Low | Some broad documentation claims use fixed file counts. | Replaced the fixed Python-file counts in `.pre-commit-config.yaml`, `.github/workflows/checks.yml`, `docs/HARDENING-PLAN.md`, `docs/PRE-COMMIT.md`, `README.md`, and `pyproject.toml` with non-drifting wording ("all Python files" for the lint scope, "most of the Python files" for the `ruff format` reach), so the narrative no longer embeds a count that goes stale as examples and services are added. | Keep counts out of narrative text; re-derive with `git ls-files '*.py' \| wc -l` or `ruff format --check` when a number is actually needed. |
| Medium | The existing `docs/REPO-AUDIT.md` is historical and its scope is stale. | `docs/REPO-AUDIT.md` now carries a historical-document banner at the top that labels its counts (312 files, 8 examples, 3 Terraform trees, 234 tests) as 2026-08-14 snapshots and links this current report. | Keep the banner in sync if the file is updated; treat its counts as historical, not live. |
| Medium | Python support is overstated for the e2e example. | `QUICKSTART.md` now lists `e2e-agent` among the 3.10+ exceptions (and its 3.11 Docker image), and `examples/e2e-agent/README.md` documents the 3.10+ local floor and why (the source uses `str | None` union syntax, a runtime `TypeError` on 3.9). The repository-wide floor stays 3.9 for the zero-dependency examples. | Add a per-example note when an example raises its floor above the repo-wide one. |
| Medium | Deployment guides omit the staging environment. | `infra/terraform-aws/HOW-TO-DEPLOY.md` adds a staging section documenting `envs/staging/` as a release-rehearsal root; `infra/terraform-azure/HOW-TO-DEPLOY.md` and `infra/terraform-gcp/HOW-TO-DEPLOY.md` mark `envs/staging/` as an internal validation root. The Azure and GCP handler source trees (`src/`) are now present, and the staging sections have been updated to reflect that. | Keep staging sections in sync when handler source or deployment status changes. |
| Medium | The docs-preview output is easy to mistake for source. | `docs-preview/` is now in the root `.gitignore`; `README.md` documents the local build and cleanup command (`rm -rf docs-preview`); `tests/test_docs_preview.py::test_repo_preview_builds` now writes its output to a temp directory instead of the repo root, fixing the test-hygiene defect that left HTML in the worktree. | Keep `docs-preview/` ignored; do not point the test back at the repo root. |
| Medium | `audit-claims.txt` is an untracked search artifact, not repository source. | `audit-claims.txt` is now in the root `.gitignore`; any stray copy in the worktree was removed. | Regenerate-and-delete it during audits; do not commit. |

## Open discrepancies

None. All consolidation candidates in the section below have been resolved.

## Generated or unnecessary working-tree files

These should not be committed:

- `docs-preview/` — generated static HTML preview.
- `graphify-out/` — generated repository graph output.
- `.pytest_cache/` — pytest cache.
- `.ruff_cache/` — Ruff cache.
- `audit-claims.txt` — temporary audit output.
- Any `__pycache__/` directory or `*.pyc` file.

The root `.gitignore` now covers all of these. None of them are tracked; `graphify-out/` is regenerated by the pre-commit graphify hook and may reappear after any commit, and `.ruff_cache/` may reappear after a local `ruff` run — both are ignored. The others may appear during local validation and should be deleted before sharing a clean tree.

The docs-preview test previously wrote to the repository root and did not clean up — a confirmed test-hygiene defect that left stageable HTML in the worktree. `tests/test_docs_preview.py::test_repo_preview_builds` now writes its output to a temp directory, so a full test run no longer stages the preview.

## Consolidation decisions

| Candidate | Decision | Action taken |
| --- | --- | --- |
| `docs/REPO-AUDIT.md` | **Retained.** The root of the historical remediation record; `HARDENING-PLAN.md` and `checks.yml` both reference it by task number. | Already carries a historical-document banner (added in the previous commit). No further action. |
| `docs/CONCEPTS-PLAN.md` | **Removed.** All 9 tasks complete; the three concepts shipped as `agentic-system-architecture/HARNESS-ENGINEERING.md`, `CONTEXT-ENGINEERING.md`, and a deepened BUILDING-BLOCKS §4; all three sources are in `REFERENCES.md`. | Deleted. Updated the three remaining references (`README.md` file tree, `ENHANCEMENT-PLAN.md` docs index, `REPO-AUDIT.md` inline reference). |
| `docs/HARDENING-PLAN.md` | **Retained.** All 11 tasks complete, but the plan carries unique rationale narrative (the task-11 contradiction discovery, the per-task "why this exists") not fully captured in the shipped controls. | Added a historical-document banner linking to the shipped artifacts and this report. |
| `trace_eval_service/` and `services/trace-eval-service/` | **Retained (distinct roles).** `trace_eval_service/` is the importable FastAPI package (the scoring logic, tested by `test_trace_eval_service.py`, run by the Dockerfile as `trace_eval_service.app:app`). `services/trace-eval-service/` is the container layer (Dockerfile, docker-compose, runtime requirements, README). | Removed the dead `services/trace-eval-service/app.py` re-export shim — nothing imported it (the Dockerfile CMD runs `trace_eval_service.app:app` directly). The container layer keeps its Dockerfile, compose, requirements, and README. |
| `examples/rag-faiss/` and `examples/rag-langchain/` | **Retained (explicit framework comparison).** The README, QUICKSTART, and `DECISION-LOGS/0004` all frame the pair as a raw-FAISS vs LangChain comparison — `rag-langchain` is "the `rag-faiss` set plus LangChain." Both are referenced across the architecture docs, SECURITY.md, CI, and Dependabot. | No action. The framework comparison is an explicit supported goal. |
| `examples/hermes-dashboard/requirements.txt` | **Removed.** The CI `example-deps.yml` workflow already installs from `backend/requirements.txt` and labels the root file "an unused duplicate." The docker-compose and README use `backend/requirements.txt`. | Deleted the root duplicate. Added `pydantic==2.11.7` to `backend/requirements.txt` (the backend app imports it directly; the root file had it, the backend file relied on fastapi's transitive pull). Updated `example_deps.py` to gather pins from all `requirements.txt` files under an example (not just the top-level one), so the dependency checker reads the canonical manifest. |
| Module-level `.terraform.lock.hcl` files | **Removed (44 files).** CI runs `terraform init` only at the 14 env roots; tflint reads HCL directly without init; modules are validated through the roots that call them. | Deleted all 44 module-level lock files. Added a `.gitignore` rule (`infra/terraform-*/modules/*/.terraform.lock.hcl`) so a local `terraform init` inside a module does not re-stage them. The 14 env-root locks remain as the source of truth. |

## Verification performed

- Enhancement plan contains 45 numbered tasks.
- All 45 tasks are `Done`. Task 6 (`terraform plan` in CI) was closed in favor of the
  existing `validate` coverage — `plan` requires cloud credentials that break the
  no-secrets CI constraint.
- The full repository unittest suite passes after installing `tests/requirements.txt` (`310 tests,
  21 skipped`). The FastAPI/OpenTelemetry dependency gap and missing security classifications
  identified by the clean-environment audit are now resolved.
- The worktree is clean of generated artifacts; the audit report is committed.
- Current Python file count: 130 tracked files total, 123 in checked directories (examples/, infra/*/src/, tests/, .github/scripts/); the remaining 7 are 5 infra tree tests and the 2-file `trace_eval_service/` package. `services/trace-eval-service/` is a container layer (Dockerfile, compose, requirements, README) with no .py files after the dead shim was removed.

## Follow-up order

1. ~~Correct the confirmed "three clouds/trees" wording - done~~
2. ~~Remove temporary generated files from local worktrees - done~~
3. ~~Decide whether the historical planning documents remain useful - done~~ (CONCEPTS-PLAN removed, REPO-AUDIT and HARDENING-PLAN retained with banners)
4. ~~Decide whether the two trace-eval service paths and the two RAG examples are intentionally distinct - done~~ (trace-eval paths retained with distinct roles, dead shim removed; RAG examples retained as an explicit framework comparison)
