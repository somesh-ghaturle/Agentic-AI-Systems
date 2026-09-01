# Repository discrepancies and cleanup candidates

**Audit date:** 2026-09-01
**Scope:** tracked source, documentation, CI configuration, Terraform trees, examples, tests, and
generated working-tree artifacts.

This is a current-state audit, not a cleanup authorization. Items under **Future removal** are
intentionally left in place until their replacement or migration is agreed and verified.

## Confirmed discrepancies

| Severity | Finding | Evidence | Recommended action |
| --- | --- | --- | --- |
| High | The repository has five Terraform trees, but several documents still describe only three clouds or three trees. | `README.md:50`, `SECURITY.md:20-34`, `.github/workflows/codeql.yml`, `.github/ISSUE_TEMPLATE/security.md`, and `docs/agentic-system-architecture/README.md` omit Snowflake and/or the hybrid POC. | Normalize wording to distinguish four cloud/data-platform trees plus the opt-in hybrid POC. |
| Medium | The existing `docs/REPO-AUDIT.md` is historical and its scope is stale. | Its header reports 312 tracked files, 8 examples, 3 Terraform trees, and 234 tests; the current repository has 591 tracked files, 20 example directories, 5 Terraform trees, and 27 test files. | Keep it as historical remediation history, but link this current report and label the old counts as historical. |
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

## Future removal or consolidation candidates

| Candidate | Why flag it | Removal condition |
| --- | --- | --- |
| `docs/REPO-AUDIT.md` | Large historical remediation plan overlaps with this current-state report. | Retain only if its historical decisions are still useful; otherwise archive it or merge durable findings into this file. |
| `docs/CONCEPTS-PLAN.md` | Planning document with historical example counts and overlapping roadmap material. | Remove or archive after confirming every still-relevant concept is represented in `ROADMAP.md` or implementation docs. |
| `docs/HARDENING-PLAN.md` | Older hardening plan overlaps with `SECURITY.md`, `THREAT-MODEL.md`, and CI configuration. | Consolidate after checking that no unique control rationale or verification command would be lost. |
| `trace_eval_service/` and `services/trace-eval-service/` | Two service locations may represent overlapping trace-evaluation entry points. | Keep both only while the root wrapper and container service have distinct supported deployment roles; otherwise choose one canonical path. |
| `examples/rag-faiss/` and `examples/rag-langchain/` | Similar RAG examples with different dependency footprints increase maintenance and dependency-scanning cost. | Retain both only if the framework comparison is an explicit supported goal; otherwise designate one canonical example. |
| Terraform provider lock files under every module and environment | Many lock files are intentional for isolated validation, but they create update and platform-drift maintenance. | Consolidate only after CI proves a shared lock strategy works for all roots and architectures. |

## Verification performed

- Enhancement plan contains 45 numbered tasks.
- Current status rows contain 43 `Done`, 1 `Verified`, and 1 `Blocked` task.
- Task 6 (`terraform plan` in CI) remains blocked because enabling it requires a deliberate
  cloud-credential and access-policy decision.
- Focused regression suites passed for the Snowflake infrastructure and newly added backlog
  examples.
- The worktree should be cleaned of generated artifacts before the audit report is committed.

## Follow-up order

1. Correct the confirmed “three clouds/trees” wording and stale fixed counts.
2. Remove temporary generated files from local worktrees.
3. Decide whether the historical planning documents remain useful.
4. Decide whether the two trace-eval service paths and the two RAG examples are intentionally
   distinct.
