# Repository discrepancies and cleanup candidates

**Audit date:** 2026-09-01
**Scope:** tracked source, documentation, CI configuration, Terraform trees, examples, tests, and
generated working-tree artifacts.

This is a current-state audit, not a cleanup authorization. Items under **Future removal** are
intentionally left in place until their replacement or migration is agreed and verified.

## Confirmed discrepancies

| Severity | Finding | Evidence | Recommended action |
| --- | --- | --- | --- |
| Critical | CI is not self-contained for the full test suite. | **Resolved:** `tests/requirements.txt` pins FastAPI, OpenTelemetry, and HTTP test dependencies; the main checks workflow installs it before unittest discovery. | Keep the test manifest pinned and update it when dependency-bearing suites change. |
| High | The security-policy test does not include all current examples. | **Resolved:** `SECURITY.md` now classifies `edge-agent`, `hermes-dashboard`, and `memory-agent`, and their READMEs carry the required disclaimer. | Keep the policy test as the source-of-truth guard. |
| High | The repository has five Terraform trees, but several documents still describe only three clouds or three trees. | `README.md:50`, `SECURITY.md:20-34`, `.github/workflows/codeql.yml`, `.github/ISSUE_TEMPLATE/security.md`, and `docs/agentic-system-architecture/README.md` omit Snowflake and/or the hybrid POC. | Normalize wording to distinguish four cloud/data-platform trees plus the opt-in hybrid POC. |
| High | The infrastructure module catalog contains stale resource names and interfaces. | `infra/MODULES.md` and the Azure/GCP approval READMEs reference Terraform resources or arguments that do not exist in the corresponding source/provider schema. | Reconcile catalog entries against each module's current `.tf` files and provider schemas. |
| High | Dependency automation omits current dependency manifests. | `.github/workflows/example-deps.yml` omits the dashboard and memory-agent; `.github/dependabot.yml` omits graph-agent, dashboard, memory-agent, and the trace-eval service. | Add all supported manifests to CI and Dependabot, or document why a manifest is intentionally excluded. |
| High | Service changes can bypass CI and CodeQL. | **Resolved:** `.github/workflows/checks.yml` and `.github/workflows/codeql.yml` now trigger for `services/**` on pushes and pull requests. | Keep service paths in sync when adding new service trees. |
| Medium | The existing `docs/REPO-AUDIT.md` is historical and its scope is stale. | Its header reports 312 tracked files, 8 examples, 3 Terraform trees, and 234 tests; the current repository has 591 tracked files, 20 example directories, 5 Terraform trees, and 27 test files. | Keep it as historical remediation history, but link this current report and label the old counts as historical. |
| Medium | Python support is overstated for the e2e example. | The repository advertises Python 3.9+, while `examples/e2e-agent/app.py` uses `str | None` without postponed annotations and its Dockerfile requires Python 3.11. | Raise the documented floor or make the example compatible with the stated floor. |
| Medium | Deployment guides omit the staging environment. | `infra/terraform-aws/HOW-TO-DEPLOY.md`, `infra/terraform-azure/HOW-TO-DEPLOY.md`, and `infra/terraform-gcp/HOW-TO-DEPLOY.md` do not document their `envs/staging` roots. | Add staging guidance or explicitly mark staging as an internal validation root. |
| Medium | The docs-preview output is easy to mistake for source. | `docs-preview/` contains generated HTML and is currently untracked; the workflow intentionally uploads it as an artifact. | Keep it out of Git and add an explicit local cleanup command to the preview documentation. |
| Medium | `audit-claims.txt` is an untracked search artifact, not repository source. | It contains raw grep output from the audit process. | Remove it after this report is committed. |
| Low | Status language is not uniform in the enhancement plan. | Most completed rows use `Done`; Task 17 uses `Verified`, while the introduction distinguishes both states. | Either verify every completed task or use one completion state consistently. |
| Low | Some broad documentation claims use fixed file counts. | `.pre-commit-config.yaml`, `.github/workflows/checks.yml`, and `docs/HARDENING-PLAN.md` refer to “86 Python files”; the repository has since gained additional examples and services. | Replace fixed counts with commands or “all Python files” wording. |

## Generated or unnecessary working-tree files

These should not be committed:

- `docs-preview/` — generated static HTML preview.
- `graphify-out/` — generated repository graph output.
- `.pytest_cache/` — pytest cache.
- `.ruff_cache/` — Ruff cache.
- `audit-claims.txt` — temporary audit output.
- Any `__pycache__/` directory or `*.pyc` file.

The root `.gitignore` already covers most of these. The current untracked preview and audit files
were created by local validation and should be deleted before sharing or committing a clean tree.

The docs-preview test currently writes to the repository root (`tests/test_docs_preview.py`) and
does not clean that directory afterward. This is a confirmed test-hygiene defect, not merely a
developer habit: a full test run leaves stageable HTML files in the worktree.

## Future removal or consolidation candidates

| Candidate | Why flag it | Removal condition |
| --- | --- | --- |
| `docs/REPO-AUDIT.md` | Large historical remediation plan overlaps with this current-state report. | Retain only if its historical decisions are still useful; otherwise archive it or merge durable findings into this file. |
| `docs/CONCEPTS-PLAN.md` | Planning document with historical example counts and overlapping roadmap material. | Remove or archive after confirming every still-relevant concept is represented in `ROADMAP.md` or implementation docs. |
| `docs/HARDENING-PLAN.md` | Older hardening plan overlaps with `SECURITY.md`, `THREAT-MODEL.md`, and CI configuration. | Consolidate after checking that no unique control rationale or verification command would be lost. |
| `trace_eval_service/` and `services/trace-eval-service/` | Two service locations may represent overlapping trace-evaluation entry points. | Keep both only while the root wrapper and container service have distinct supported deployment roles; otherwise choose one canonical path. |
| `examples/rag-faiss/` and `examples/rag-langchain/` | Similar RAG examples with different dependency footprints increase maintenance and dependency-scanning cost. | Retain both only if the framework comparison is an explicit supported goal; otherwise designate one canonical example. |
| `examples/hermes-dashboard/requirements.txt` | Duplicates `examples/hermes-dashboard/backend/requirements.txt`, while the compose file and README use the backend manifest. | Remove the root duplicate after CI and local setup instructions use one canonical manifest. |
| Module-level `.terraform.lock.hcl` files | Reusable modules carry lock files in addition to environment-root locks, increasing update and platform-drift maintenance. | Consolidate only after CI proves a shared lock strategy works for all roots and architectures. |

## Verification performed

- Enhancement plan contains 45 numbered tasks.
- Current status rows contain 43 `Done`, 1 `Verified`, and 1 `Blocked` task.
- Task 6 (`terraform plan` in CI) remains blocked because enabling it requires a deliberate
  cloud-credential and access-policy decision.
- The full repository unittest suite passes after installing `tests/requirements.txt` (`310 tests,
  21 skipped`). The FastAPI/OpenTelemetry dependency gap and missing security classifications
  identified by the clean-environment audit are now resolved.
- The worktree should be cleaned of generated artifacts before the audit report is committed.

## Follow-up order

1. Correct the confirmed “three clouds/trees” wording and stale fixed counts.
2. Remove temporary generated files from local worktrees.
3. Decide whether the historical planning documents remain useful.
4. Decide whether the two trace-eval service paths and the two RAG examples are intentionally
   distinct.
