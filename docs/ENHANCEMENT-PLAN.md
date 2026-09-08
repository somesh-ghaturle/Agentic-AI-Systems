# Enhancement Plan — Strategic Improvements

A centralized tracking document for all planned enhancements to the Agentic-AI-Systems repository.
Each item was derived from the repository's current state and strategic goals. Nothing here is
inferred from summaries — every task is actionable and testable.

**Scope:** Repository-wide improvements across examples, infrastructure, documentation, CI/CD,
security, and community adoption.

**How to use this document.** Work top to bottom, phase by phase. Each task carries:

- A clear **Goal** (what we want to achieve)
- The **Action** (exact steps to take)
- **Verification** (command or check to confirm it works)
- **Priority** (High/Medium/Low)

Update the status column as you go: `Not Started` → `In Progress` → `Done` → `Verified`. A task
whose own Verify block cannot pass as written is marked `Blocked` and carries a note in its
section saying what has to be decided first.

---

## Priority Matrix

| Priority | Criteria | SLA |
| ---------- | ---------- | ----- |
| High | Security hardening, critical gaps, blocks other work | 7 days |
| Medium | Functional improvements, new examples, docs | 30 days |
| Low | Nice-to-haves, refinements, future ideas | 90 days |

---

## Progress

| # | Task | Category | Priority | Status | Owner | Due Date |
| --- | ------ | ---------- | ---------- | -------- | ------- | ---------- |
| 1 | Add `QUICKSTART.md` | Documentation | High | Done | | 2026-08-20 |
| 2 | Add pre-commit hooks | Repository | High | Done | | 2026-08-20 |
| 3 | Label good first issues in GitHub | Community | High | Done | | 2026-08-20 |
| 4 | Document approval token TTL | Infrastructure | High | Done | | 2026-08-23 |
| 5 | Add secret scanning to CI | Security | High | Done | | 2026-08-23 |
| 6 | Add `terraform plan` to CI | CI/CD | High | Done | Closed in favor of `validate`; plan requires cloud credentials that break the no-secrets CI constraint | 2026-09-01 |
| 7 | Add `MODULES.md` catalog | Documentation | High | Done | | 2026-08-23 |
| 8 | Add `checkpoint-agent` example | Examples | High | Done | | 2026-08-23 |
| 9 | Add `SECURITY.md` tests to CI | Security | High | Done | | 2026-08-30 |
| 10 | Document handler packaging divergence | Documentation | Medium | Done | | 2026-08-30 |
| 11 | Add SAST scanning to CI | Security | High | Done | | 2026-08-30 |
| 12 | Add issue templates | Community | High | Done | | 2026-08-23 |
| 13 | Document approval claim formats | Documentation | High | Done | | 2026-08-23 |
| 14 | Add `envs/staging` | Infrastructure | Medium | Done | | 2026-08-30 |
| 15 | Add Terraform policy-as-code (OPA) | Infrastructure | Medium | Done | | 2026-09-13 |
| 16 | Add `DECISION-LOGS/` with ADRs | Documentation | Medium | Done | | 2026-08-30 |
| 17 | Add cost monitoring module | Infrastructure | Medium | Done | | 2026-09-20 |
| 18 | Document secrets rotation | Infrastructure | Medium | Done | | 2026-09-06 |
| 19 | Add `HOW-TO-RECOVER.md` per cloud | Infrastructure | Medium | Done | | 2026-09-13 |
| 20 | Add `multi-agent-debate` example | Examples | Medium | Done | | 2026-09-06 |
| 21 | Add `tool-discovery` example | Examples | Medium | Done | | 2026-09-13 |
| 22 | Add `context-overflow` example | Examples | Medium | Done | | 2026-09-20 |
| 23 | Add `eval-red-teaming` example | Examples | Medium | Done | | 2026-09-27 |
| 24 | Update `graph-agent` for production | Examples | Medium | Done | | 2026-09-06 |
| 25 | Add `MIGRATION-GUIDE.md` | Documentation | Medium | Done | | 2026-09-13 |
| 26 | Add example dependency graph to CI | CI/CD | Medium | Done | | 2026-09-06 |
| 27 | Add performance tests to CI | CI/CD | Medium | Done | | 2026-09-20 |
| 28 | Add runtime smoke tests to CI | CI/CD | Medium | Done | | 2026-09-13 |
| 29 | Add `terraform plan` cost estimation | CI/CD | Medium | Done | | 2026-09-20 |
| 30 | Add approval gate fuzzing | Security | Medium | Done | | 2026-09-20 |
| 31 | Update `THREAT-MODEL.md` | Security | Medium | Done | | 2026-09-13 |
| 32 | Add `COMPLIANCE.md` | Documentation | Low | Done | | 2026-10-11 |
| 33 | Add discussion topics | Community | Low | Done | | 2026-10-04 |
| 34 | Add `ROADMAP.md` | Community | Low | Done | | 2026-09-13 |
| 35 | Add badges to README | Community | Low | Done | | 2026-10-11 |
| 36 | Add `CITATION.cff` | Community | Low | Done | | 2026-10-18 |
| 37 | Convert Mermaid diagrams to code | Documentation | Low | Done | | 2026-10-04 |
| 38 | Add automated docs preview | CI/CD | Low | Done | | 2026-10-04 |
| 39 | Add `FAQ.md` | Documentation | Medium | Done | | 2026-09-06 |
| 40 | Add evaluation as a service | Future | Medium | Done | | 2026-09-27 |
| 41 | Add model routing to `hermes-agent` | Future | Medium | Done | Deterministic offline `ModelRouter` profiles and focused tests | 2026-10-04 |
| 42 | Add `memory-agent` example | Future | Medium | Done | Dependency-free vector, graph, decay, and session stores | 2026-10-18 |
| 43 | Hybrid cloud proof-of-concept | Future | Low | Done | Opt-in Terraform topology; all resources disabled by default | 2026-11-01 |
| 44 | Edge agents proof-of-concept | Future | Low | Done | Offline SQLite state, file approval gate, and unprivileged container | 2026-11-15 |
| 45 | Human-in-the-loop UX dashboard | Future | Low | Done | React/FastAPI dashboard with WebSocket approval updates | 2026-11-01 |
| 46 | Fix the GCP `reason` model/thinking mismatch | Infrastructure | High | Done | Pinned model predated the adaptive-thinking call it was paired with | 2026-09-10 |
| 47 | Complete the `e2e-agent` test dependency guard | CI/CD | High | Done | Guard named one of four imports; partial envs failed for the wrong reason | 2026-09-10 |
| 48 | Audit model pins across the four trees | Infrastructure | Medium | Done | Allowlist test; Snowflake held back deliberately, cross-region inference | 2026-10-03 |
| 49 | Refresh `hermes-agent` router model profiles | Examples | Medium | Done | Ratios replace prices; tier ordering is now the assertion | 2026-10-03 |
| 50 | Revisit the `py39` floor | Repository | Low | Done | Floor kept and now tested; it had never been exercised | 2026-12-01 |
| 51 | Re-evaluate ADR 0002 against Claude on Foundry | Documentation | Low | Done | Condition tested 2026-09-03 and not met; decision stands | 2026-12-01 |
| 52 | Add an MCP server example behind the write boundary | Examples | Medium | Done | 19 tests, two mutations; discovery is not authorization | 2026-10-31 |
| 53 | Fix the red `lint` job | CI/CD | High | Done | 11 ruff findings across three files; two commits' worth of drift | 2026-09-13 |
| 54 | Fix the red `examples` job | CI/CD | High | Done | Three examples ship an `agent.py`; a bare import bound one for the whole run | 2026-09-13 |
| 55 | Pin `hashicorp/setup-terraform` to a commit SHA | Security | High | Done | CodeQL `actions/unpinned-tag`, both call sites | 2026-09-13 |
| 56 | Harden the docs-preview markdown renderer | Security | High | Done | Attribute injection through a link target, and `javascript:` hrefs | 2026-09-13 |
| 57 | Add `EVALUATION-ENGINEERING.md` | Documentation | Medium | Done | The feedback edge had two examples and no chapter | 2026-10-06 |
| 58 | Add `ENVIRONMENT-ENGINEERING.md` | Documentation | Medium | Done | Blast radius, failure direction, and the sandbox fidelity gap | 2026-10-06 |
| 59 | Add the `second-path` example | Examples | Medium | Done | 16 tests, four mutations; the gate suite passes while the boundary is open | 2026-10-06 |
| 60 | Cover harness and environment in the design review | Documentation | High | Done | The checklist ran for two chapters without covering either | 2026-09-13 |
| 61 | Rewrite `ROADMAP.md` against the current tree | Documentation | Medium | Done | Was 5 weeks stale; named none of the four chapters | 2026-10-06 |
| 62 | Add `budget-guard` to the root README tree | Documentation | Low | Done | 22 of 23 examples were listed | 2026-12-06 |
| 63 | Diagram the hybrid Terraform tree | Documentation | Medium | Done | The only architecture document without one | 2026-10-06 |
| 64 | Check documented counts against the tree | CI/CD | High | Done | 17 claims; found 10 stale numbers and caught 2 of its author's | 2026-09-13 |
| 65 | State the VPC-only collection's reachability gap | Documentation | Medium | Done | Prod locks the collection to an endpoint no handler can reach | 2026-09-07 |
| 66 | Correct the module chart and carry the reachability guard to Azure | Documentation | Medium | Done | Two wrong notes, a missing fifth tree, and the same gap one variable away in Azure | 2026-09-07 |
| 67 | Fix the red `lint` job on `main` | CI/CD | High | Done | Four ruff findings in the two guard suites tasks 65 and 66 added | 2026-09-08 |

**Status verified 2026-09-01** by running each task's own **Verify** block against the working
tree, and kept current as tasks have landed since. **All 67 tasks are now `Done`**, the last of
them — 53 through 64 — on 2026-09-06, 65 and 66 on 2026-09-07, and 67 on 2026-09-08.

Tasks 53 through 56 are unlike the rest of this plan: they were not planned. Two CI jobs were
found red on `main` — `lint` and `examples` — and two security findings were open, one raised by
CodeQL and one found while reading the docs-preview renderer. They are recorded here because a
plan that only lists intended work makes the tree look tidier than it was, and because both CI
failures were introduced by earlier tasks in this same document.

This paragraph previously read "Thirty-three tasks now pass", listed thirty-six numbers, and
recorded task 6 as `Blocked` while the table above it said `Done`. All three were stale. It is
worth leaving the correction visible rather than quietly overwriting it: a summary that
contradicts the table it summarises is the same failure this plan keeps finding in the tree —
a check that looks authoritative and verifies nothing — and prose is where it hides longest,
because nothing runs it.

Task 6 was closed in favour of `terraform validate`: `plan` needs cloud credentials, and the
no-secrets constraint on CI is worth more than the extra coverage. That is a decision, not a
blockage, and the table records it as such.

Twelve rows — 17, 22, 23, 29, 30, and 32 through 38 — have no detail section below. Those are
the tasks whose table entry said everything there was to say. Tasks 1 through 16 and 40 through
45 carry no `**Status:**` line either; they predate that convention, and their status lives in
the table. Neither is a gap to close, but both are worth naming so the next reader does not
mistake the absence for an omission.

Tasks 4 and 8 were verified rather than written — their artifacts already existed. Task 4 passes
cleanly: all three `modules/approval/README.md` files carry the `Token Lifetime and Rotation`
section, which also clears the blocker recorded against it earlier. Task 8 needed two fixes before
it passed; see its Verify block.

Task 5 is worth a note on how it got to `Done`. A `secret-scan` job matching this document's draft
had already been added to `checks.yml`, so the task looked finished. It was not: the job installed
an unpinned scanner, called a subcommand 8.30 had removed, and ran against a shallow clone that
gave it one commit of history to look at. Copying a plan's YAML is not the same as running it —
which is the same lesson task 2's terraform hook taught, where the hook reported `Passed` while
silently skipping the first file it was handed.

Task 35 shipped without a Terraform version badge, because the repository stated three different
Terraform versions and the badge could not be honest until one won: `required_version` in the
`.tf` files said `>= 1.6`, `checks.yml` pinned `1.15.8`, and `QUICKSTART.md` told the reader to
install `1.9.8+`.

**Resolved 2026-08-23, and the badge is now in `README.md`.** `QUICKSTART.md` was the number with
nothing behind it: `1.9.8+` matched neither the declared floor nor the pin CI proves. It now says
`1.6+`, and the badge states the same. The other two stay as they are on purpose — a floor and a
CI pin answer different questions, and hardening Task 9 in [HARDENING-PLAN.md](HARDENING-PLAN.md)
records why, along with the one thing still unproven: nothing actually tests 1.6.

A related gap the badge exposes rather than causes: the `Python 3.9+` badge repeats the support
floor that `README.md`, `QUICKSTART.md`, and `CONTRIBUTING.md` all state, but every CI job runs on
`3.12` alone. Nothing verifies that the examples still import on 3.9. Either add 3.9 to a CI matrix
or raise the stated floor to the version actually tested.

**Five tasks need their definition settled before the work starts.** Their Verify block cannot
pass as written, or describes something that already exists under another name:

- **Task 6** — `terraform plan` needs cloud credentials, which the workflow header rules out on
  purpose. Filed as a Phase 1 quick win, it is really a decision about granting CI standing access
  to all four cloud/data-platform trees. See the note in its section.
- **Task 22** — `examples/context-compaction` already exists. Confirm `context-overflow` is a
  distinct scenario rather than a second name for the same one.
- **Task 26** — `.github/workflows/example-deps.yml` already installs each example's pinned
  requirements in isolation and imports every entry module. The cycle detection is the only
  coverage `scripts/dependency_graph.py` adds; scope the task against what already runs.
- **Task 31** — has no detail section, and `docs/THREAT-MODEL.md` was written in the same batch as
  this plan. What the update should add is undefined.
- **Task 41** — `examples/hermes-agent/hermes/router.py` already held `Router`, which routes
  intents to approval and execution. `ModelRouter` is now a separate deterministic model-choice
  seam, so model selection cannot call a provider or alter the write boundary.

---

## Phase 1 — Quick Wins (Week 1: 2026-08-16 to 2026-08-23)

This phase focuses on **high-impact, low-effort** tasks that improve onboarding, security,
and maintainability immediately.

### Task 1 — Add `QUICKSTART.md`

**Goal.** Reduce onboarding friction with a step-by-step guide.

**Action.**
Create `QUICKSTART.md` at the repository root with three sections:

1. **Run locally:** `python3 examples/hermes-agent/agent.py "restart the billing service"`
2. **Deploy to dev:** Step-by-step for `infra/terraform-aws/envs/dev`
3. **Trace end-to-end:** Using `trace-eval` to verify the write boundary

Include prerequisites (Python 3.9+, Terraform 1.6+) and expected output. The Terraform floor
was written here as `1.9.8+` and shipped that way; it was corrected to `1.6+` on 2026-08-23,
when that number turned out to match neither the declared floor nor the version CI proves —
see the note under Progress.

**Verify.**

```bash
test -f QUICKSTART.md && grep -c "hermes-agent\|terraform-aws\|trace-eval" QUICKSTART.md
```

---

### Task 2 — Add pre-commit hooks

**Goal.** Catch errors before they reach CI.

**Action.**
Add `.pre-commit-config.yaml` to the repository root:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
  - repo: local
    hooks:
      - id: terraform-validate
        name: terraform validate
        entry: bash -c 'rc=0; for dir in $(printf "%s\n" "$@" | xargs -n1 dirname | sort -u); do (cd "$dir" && terraform init -backend=false -input=false -no-color >/dev/null && terraform validate -no-color) || rc=1; done; exit $rc' --
        language: system
        pass_filenames: true
        files: ^infra/.*\.(tf|tfvars)$
      - id: python-compile
        name: python compile
        entry: python3 -m py_compile
        language: system
        files: \.py$
```

The terraform entry is intricate for two reasons, both found by testing it rather than reading it:

`terraform validate` has no `-recursive` flag — that belongs to `terraform fmt` — and it requires an
initialized working directory. So the hook cannot make one call from `infra/`; it has to init and
validate each changed directory, deduplicated so a three-file module change does not init three times.

The trailing `--` is load-bearing. pre-commit appends filenames to the entry, and `bash -c SCRIPT a b`
binds `a` to `$0` rather than `$1`, so `"$@"` silently drops the first file. A commit touching one
`.tf` file would have validated nothing and still reported `Passed`.

Add a `PRE-COMMIT.md` in `docs/` explaining how to install and use hooks.

**Verify.**

```bash
pre-commit run --all-files 2>&1 | grep -E "(Passed|Failed)" || echo "pre-commit not installed"
grep -q "pre-commit" CONTRIBUTING.md || echo "Add pre-commit setup to CONTRIBUTING.md"
```

---

### Task 3 — Label good first issues in GitHub

**Goal.** Encourage community contributions by tagging beginner-friendly tasks.

**Resolved 2026-08-19.** This task originally specified a new `GOOD-FIRST-ISSUE` label
(`#70c87c`), and creating it produced exactly the outcome the task was warned about: the
repository carried two labels with the identical description "Good for newcomers", so a
contributor filtering on either saw half the queue. The custom label has been deleted and
GitHub's default `good first issue` (`#7057ff`) kept.

The direction of that fix is not a style preference. `good first issue` is the exact string
GitHub reads for its own contributor discovery — the repository's `/contribute` page and the
newcomer search filters key on it. A renamed variant is invisible to all of them, so adopting a
custom name would have cost the repository the surfaces that bring first-time contributors to it.
Neither label was applied to any issue at the time, so nothing was reclassified.

**Action.**

1. Use GitHub's default `good first issue` label (`#7057ff`). Do not create a renamed variant.
2. Label these tasks:
   - Add `MODULES.md` catalog (Task 7)
   - Add pre-commit hooks (Task 2)
   - Add `FAQ.md` (Task 39)
   - Convert Mermaid diagrams to code (Task 37)
3. Document the label in `CONTRIBUTING.md`

Tasks 2 and 7 are now `Done`, so of the four listed only 37 and 39 are still available to label.

**Verify.**

```bash
# The label exists...
gh label list --limit 100 | grep -q "good first issue" && echo "Label exists" || echo "Label missing"

# ...and it is the only newcomer label, which is the condition that actually broke.
test "$(gh label list --limit 100 | grep -ci 'good.first.issue')" -eq 1 \
  && echo "exactly one newcomer label" || echo "duplicate newcomer labels"
```

---

### Task 4 — Document approval token TTL

**Goal.** Close a critical documentation gap in the write boundary.

**Action.**
Add a new section to each of:

- `infra/terraform-aws/modules/approval/README.md`
- `infra/terraform-azure/modules/approval/README.md`
- `infra/terraform-gcp/modules/approval/README.md`

Section title: **Token Lifetime and Rotation**
Content:

```markdown
### Token Lifetime and Rotation

Approval tokens expire after **24 hours** (configurable via `var.approval_token_ttl_seconds`).

**Rotation:**
1. Generate a new token: `<cloud-specific command>`
2. Update the orchestrator's environment variable: `APPROVAL_TOKEN=...`
3. Restart the orchestrator

**Mid-execution behavior:** If a token expires during an approval flow, the action is **rejected**
and must be resubmitted with a fresh token. The system logs the expiration and returns a
403 Forbidden to the caller.

**Security note:** Tokens are single-use and bound to a specific action fingerprint.
```

**Verify.**

```bash
for f in infra/terraform-{aws,azure,gcp}/modules/approval/README.md; do
  grep -q "Token Lifetime and Rotation" "$f" && echo "$f: OK" || echo "$f: MISSING"
done
```

---

### Task 5 — Add secret scanning to CI

**Goal.** Prevent accidental credential commits.

**Action.**
Add a `secret-scan` job to `.github/workflows/checks.yml` that installs a pinned, checksummed
gitleaks release binary and scans full history, plus a `.gitleaks.toml` at the repository root.
Add `.gitleaks.toml` to both path filters so a change to the allowlist retriggers the workflow.

Four corrections were needed against the first draft of this task, each found by running it:

**`fetch-depth: 0` is required.** `actions/checkout` defaults to a single-commit shallow clone.
gitleaks scans history, so the default hands it one commit and a credential committed then
deleted three commits later scans clean — the one case history scanning exists to catch. This
repo reports 56 commits scanned at full depth and 1 at `--depth 1`.

**`gitleaks detect` no longer exists.** 8.30 lists `git`, `dir`, and `stdin`; `detect` is gone
from the command list. Use `gitleaks git .`.

**`go install ...@latest` is both unpinned and slower than needed.** It pulls in the Go toolchain
to compile from source a binary the project already publishes prebuilt, and `@latest` means the
ruleset can change between two runs of the same commit — a green build becomes unreproducible and
the failure lands on whoever pushes next. Pin the version and verify the SHA256.

**`--redact` is not optional.** Build logs are public. The run that catches a live key must not be
the run that republishes it.

**Verify.**

```bash
gitleaks git . --redact --verbose
echo $?  # 0 when clean, 1 when leaks are found
```

The original `gitleaks detect --source . --dry-run` cannot pass: `--dry-run` is not a gitleaks
flag in any 8.x release.

**Why `.gitleaks.toml` is part of this task, not a follow-up.** On a clean repository this job
still fails. Two documented placeholders in `examples/e2e-agent/README.md` match the
`curl-auth-header` rule — `x-api-key: local-test-key`, the value the README tells the reader to
export one line earlier. gitleaks cannot distinguish a documented placeholder from a live
credential, so the job exits 1 on first run with nothing actually wrong. The allowlist is scoped
to that literal value in that one file rather than to the path, so a real key pasted into the
same README is still caught; this was confirmed by substituting an AWS-shaped key and watching
the scan fail.

---

### Task 6 — Add `terraform plan` to CI

> **Closed 2026-09-01 — in favor of the `validate` coverage that already runs.** The
> investigation below confirmed that `terraform plan` requires real cloud credentials
> (OIDC federation into AWS, Azure, and GCP), which directly contradicts the no-secrets
> constraint this CI is built on. The existing `validate` job runs `terraform validate`
> on all 13 environment roots offline, tflint reads every module and root, checkov
> scans the HCL for misconfigurations, and conftest enforces policy. That stack catches
> the class of errors `plan` would find without introducing a credential that gets
> disabled the first time a secret expires. The YAML snippet below is retained as the
> starting point if the credential decision is ever reversed.

> **Original investigation (retained for context).** The Verify block
> was run against `infra/terraform-aws/envs/dev` on Terraform 1.15.8 and fails twice over, and the
> second failure is not a bug in the snippet but a property of `terraform plan`.
>
> **1. No variable values.** `plan` stops at `No value for required variable` for `project`,
> `approval_validator`, and `approval_executor`. `terraform.tfvars` is gitignored by design — only
> `.example` files are committed — so CI has nothing to supply unless it passes
> `-var-file=terraform.tfvars.example`.
>
> **2. No credentials, and this one is structural.** Given the example tfvars, the AWS root then
> fails with `No valid credential sources found` after trying the EC2 IMDS endpoint. `validate`
> works offline; `plan` contacts the provider. Making this job pass means federating CI into AWS,
> Azure, and GCP — three OIDC trust relationships granting read access to real environments.
>
> That directly contradicts the constraint this workflow is built on, stated in its own header:
> *"Everything here runs without cloud credentials. That is a constraint worth keeping: a check
> that needs a subscription is a check that gets disabled the first time a secret expires."*
> Task 6 is filed as a Phase 1 quick win, but it is a security-architecture decision about giving
> CI standing cloud access. Resolve it deliberately or close it in favour of the `validate`
> coverage that already runs.
>
> **3. A smaller trap in the snippet.** `-out=tfplan` writes a file that `.gitignore` does not
> cover — the pattern is `*.tfplan`, which does not match a file named exactly `tfplan`
> (`git check-ignore` confirms it is untracked). The same `.gitignore` notes plan output "can
> contain resolved secret values". Whatever this task becomes, name the output `*.tfplan`.
>
> **4. The version pin below was wrong and has been corrected.** It read `1.9.8`, which matched
> neither `checks.yml` nor the declared floor. It now reads `1.15.8`, matching the pin the `fmt`
> and `validate` jobs already use — a plan job proving a different CLI version than the rest of
> CI is drift being introduced rather than caught. The wider reconciliation closed on 2026-08-23;
> see the note under Progress and hardening Task 9.

**Goal.** Catch unintended infrastructure changes before merge.

**Action.**
Add a new job to `.github/workflows/checks.yml` that runs `terraform plan` on all seven
environment roots (AWS/dev, AWS/prod, Azure/dev, Azure/prod, Azure/tenant, GCP/dev, GCP/prod).

Use a matrix strategy:

```yaml
  terraform-plan:
    name: Terraform plan
    runs-on: ubuntu-latest
    strategy:
      matrix:
        include:
          - tree: aws
            env: dev
          - tree: aws
            env: prod
          - tree: azure
            env: dev
          - tree: azure
            env: prod
          - tree: azure
            env: tenant
          - tree: gcp
            env: dev
          - tree: gcp
            env: prod
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.15.8
      - name: Terraform init
        run: terraform -chdir=infra/terraform-${{ matrix.tree }}/envs/${{ matrix.env }} init -backend=false -input=false
      - name: Terraform plan
        run: terraform -chdir=infra/terraform-${{ matrix.tree }}/envs/${{ matrix.env }} plan -out=tfplan -input=false
      - name: Show plan
        run: terraform -chdir=infra/terraform-${{ matrix.tree }}/envs/${{ matrix.env }} show -json tfplan | python3 -c "import sys,json; d=json.load(sys.stdin); print('Changes:', len(d.get('planned_values', {}).get('root_module', {}).get('resources', [])))"
```

**Verify.**

```bash
# Test locally on one root
cd infra/terraform-aws/envs/dev && \
  terraform init -backend=false -input=false && \
  terraform plan -out=tfplan -input=false && \
  terraform show -json tfplan | python3 -c "import sys,json; print(json.load(sys.stdin)['planned_values']['root_module']['resources'])"
```

---

### Task 7 — Add `MODULES.md`

**Goal.** Central catalog of all Terraform modules.

**Action.**
Create `infra/MODULES.md` with a table:

```markdown
# Terraform Modules Catalog

This document lists all modules across the three cloud implementations.

## AWS (`terraform-aws/`)

| Module | Purpose | Dependencies | Owner | Status |
|--------|---------|--------------|-------|--------|
| approval | Enforces human approval for write actions via DynamoDB | state, tools | - | Stable |
| archive | Stores audit logs and provenance | - | - | Stable |
| knowledge | Manages OpenSearch Serverless for RAG | - | - | Stable |
| observability | CloudWatch dashboards and alarms | - | - | Stable |
| orchestration | Step Functions workflows | approval, tools | - | Stable |
| security | IAM roles, Lambda policies, Bedrock guardrails | - | - | Stable |
| state | DynamoDB tables for execution state | - | - | Stable |
| tools | Lambda functions for read/write actions | state, security | - | Stable |

## Azure (`terraform-azure/`)

| Module | Purpose | Dependencies | Owner | Status |
|--------|---------|--------------|-------|--------|
| approval | Enforces human approval for write actions via Cosmos DB | state, tools | - | Stable |
| archive | Stores audit logs and provenance | - | - | Stable |
| entra-audit | Entra ID audit alerts for approval bypass attempts | - | - | Stable |
| identity | Manages identities and role assignments | - | - | Stable |
| knowledge | Manages AI Search for RAG | - | - | Stable |
| model-integration | Azure OpenAI deployment | security | - | Stable |
| networking | VNet and subnets | - | - | Stable |
| observability | Monitor and alerts | - | - | Stable |
| orchestration | Logic Apps workflows | approval, tools | - | Stable |
| security | Security controls | - | - | Stable |
| state | Storage Tables / Cosmos DB | - | - | Stable |
| tools | Function Apps for read/write actions | state, security | - | Stable |

## GCP (`terraform-gcp/`)

| Module | Purpose | Dependencies | Owner | Status |
|--------|---------|--------------|-------|--------|
| approval | Enforces human approval for write actions via Firestore | state, tools | - | Stable |
| archive | Stores audit logs and provenance | - | - | Stable |
| identity | IAM service accounts and bindings | - | - | Stable |
| knowledge | Vertex AI Vector Search | - | - | Stable |
| model-integration | Vertex AI model deployment | security | - | Stable |
| observability | Cloud Monitoring dashboards | - | - | Stable |
| orchestration | Cloud Workflows | approval, tools | - | Stable |
| security | IAM policies, including Deny policies | - | - | Stable |
| state | Firestore for execution state | - | - | Stable |
| tools | Cloud Functions gen2 for read/write actions | state, security | - | Stable |
```

**Verify.**

```bash
test -f infra/MODULES.md && grep -c "terraform-aws\|terraform-azure\|terraform-gcp" infra/MODULES.md
```

---

### Task 12 — Add issue templates

**Goal.** Standardize bug reports, feature requests, and security disclosures.

**Action.**
Create `.github/ISSUE_TEMPLATE/` with three files:

1. **`bug_report.md`:**

```markdown
name: Bug Report
about: Report a bug in the examples, infrastructure, or documentation
title: "[BUG] "
labels: bug
type: issue

---
**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Run '...'
3. See error

**Expected behavior**
A clear description of what you expected to happen.

**Screenshots/Logs**
If applicable, add screenshots or log output to help explain your problem.

**Environment:**
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.12.0]
- Terraform version: [e.g., 1.15.8]
- Cloud: [AWS/Azure/GCP/None]

**Additional context**
Add any other context about the problem here.
```

1. **`feature_request.md`:**

```markdown
name: Feature Request
about: Suggest a new feature or enhancement
title: "[FEAT] "
labels: enhancement
type: issue

---
**Is your feature request related to a problem?**
A clear and concise description of what the problem is. Ex. I'm always frustrated when [...]

**Describe the solution you'd like**
A clear and concise description of what you want to happen.

**Describe alternatives you've considered**
A clear and concise description of any alternative solutions or features you've considered.

**Additional context**
Add any other context or screenshots about the feature request here.

**Building Blocks Alignment**
Which of the [six building blocks](docs/agentic-system-architecture/BUILDING-BLOCKS.md) does this relate to?
- [ ] Model routing
- [ ] Tools
- [ ] Memory and state
- [ ] Orchestration
- [ ] Trace-level evals
- [ ] Approval gates
- [ ] Other: ______
```

1. **`security.md`:**

```markdown
name: Security Report
about: Report a security vulnerability
labels: security
type: issue

---
**Please do not report security vulnerabilities in public issues.**

Instead, please report security vulnerabilities by emailing [YOUR_EMAIL] or using
[GitHub Security Advisories](https://docs.github.com/en/code-security/security-advisories/repository-security-advisories/about-repository-security-advisories).

**Scope:**
- Write boundary bypasses in any of the three Terraform trees
- Write boundary bypasses in `hermes-agent` or `harness-agent` examples
- Compromised approval gate implementations
- Supply chain attacks via Terraform modules

**What to include:**
- Steps to reproduce the vulnerability
- Impact assessment
- Suggested mitigation

**What NOT to include:**
- Do not create a public GitHub issue
- Do not post in discussions
- Do not disclose publicly until a fix is released

**Response SLA:**
- Critical: 24 hours
- High: 7 days
- Medium: 30 days
```

**Verify.**

```bash
ls -la .github/ISSUE_TEMPLATE/
test -f .github/ISSUE_TEMPLATE/bug_report.md && \
test -f .github/ISSUE_TEMPLATE/feature_request.md && \
test -f .github/ISSUE_TEMPLATE/security.md && \
echo "All templates present"
```

---

### Task 13 — Document approval claim formats

**Goal.** Clarify how the write boundary is enforced across clouds.

**Action.**
Add a new section to `docs/agentic-system-architecture/BUILDING-BLOCKS.md` under **Approval Gates**:

```markdown
### Approval Claim Formats by Cloud

The write boundary is enforced by binding approval to a **fingerprint** of the exact action.
Each cloud implements this differently:

| Cloud | Storage | Claim Format | Validation Method |
|-------|---------|--------------|-------------------|
| AWS | DynamoDB | `{"action":"restart_service","args":{"service":"billing"},"fingerprint":"sha256:...","expires_at":1234567890}` | Condition expression on `fingerprint` and `expires_at` |
| Azure | Cosmos DB | Same JSON structure | ETag-based conditional write |
| GCP | Firestore | Same JSON structure | Transaction with document existence check |

**Fingerprint Algorithm:**
```python
import hashlib, json

def generate_fingerprint(action: str, args: dict) -> str:
    payload = {"action": action, "args": args}
    return "sha256:" + hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
```

**Security Properties:**

- Single-use: A claim is consumed after use
- Expiring: Default TTL is 15 minutes (configurable)
- Bound to arguments: Changing any argument invalidates the claim

```

**Verify.**
```bash
grep -A 10 "Approval Claim Formats by Cloud" docs/agentic-system-architecture/BUILDING-BLOCKS.md
```

---

## Phase 2 — Infrastructure & Examples (Week 2-3: 2026-08-23 to 2026-09-06)

This phase focuses on **expanding functionality** with new examples and infrastructure improvements.

### Task 9 — Add `SECURITY.md` tests to CI

**Goal.** Stop the security policy's scope list from silently going stale.

**Why this needed writing at all.** `SECURITY.md` divides the repository into what is worth
reporting and what is not. That list decays without any visible symptom: nothing fails when an
example is added and nobody classifies it, and the person who eventually notices is a researcher
who spent an afternoon on something the maintainers never considered in scope.

Two such decays were live when the task was picked up:

- **`checkpoint-agent` and `e2e-agent` were in neither list.** checkpoint-agent had just landed.
  `e2e-agent` had been unclassified for longer and matters more — its own README advertises
  "security gating" while the example implements no approval step, so a reader has every reason
  to treat it as in scope, and the policy never said otherwise.
- **The out-of-scope paragraph asserted something untrue.** It said each of those examples "says
  in its own README that it makes no security claim." None of the nine did. `starter-agent` and
  `langchain-agent` did not mention security, production, or claims anywhere.

**Action.**

1. Classify every example in `SECURITY.md`. `e2e-agent` is the judgement call, and it resolves
   the opposite way to the rest: it goes **in** scope. It advertises itself as "Secure,
   Observable, Auditable" with "security gating", exposes an HTTP service behind an API-key
   header, and writes audit and provenance records — while implementing no approval step at all.
   A pattern that looks correct and is not, sitting in a directory whose title invites copying,
   is the harm this policy exists to catch. So reports that its gating is weaker than its README
   implies are in scope, and it is the one example that owes no disclaimer.
2. Add the promised `## Security` section to the nine out-of-scope example READMEs.
3. Add `tests/test_security_policy.py`, which reads `SECURITY.md` and asserts the tree matches it.

The module-name check parses the names out of `SECURITY.md` rather than hardcoding them. A
hardcoded list would let a typo introduced into the policy sail past the test meant to catch it.
Parsing needs the section collapsed before matching, because the list wraps mid-sentence and
reading it line by line drops whichever names land on the first line — which is exactly what the
first version did, silently returning three of the five names.

`identity` is named by the policy but has no AWS module; that tree keeps its identity policy in
`modules/orchestration` (see terraform-aws `ARCHITECTURE.md`, "Identity policy |
`modules/orchestration`"). So the test requires four modules in all three trees and requires
`identity` only to resolve somewhere. Asserting uniformity there would fail on a deliberate design
difference.

**Verify.**

```bash
python3 -m unittest tests.test_security_policy -v   # 5 tests
```

And confirm the tests constrain something, rather than passing by construction:

```bash
mkdir -p examples/zzz && echo "# tmp" > examples/zzz/README.md
python3 -m unittest tests.test_security_policy   # FAILS: unclassified example
rm -rf examples/zzz
```

All three failure modes were exercised this way — an unclassified example, a README with the
disclaimer stripped, and a phantom module name in the policy. Each fails with a message naming
the offending file.

---

### Task 10 — Document handler packaging divergence

**Goal.** Give the three-way packaging difference one place to be read, so a reader comparing the
trees can tell a deliberate divergence from an inconsistency somebody forgot to clean up.

**What was already there, and why the task still had work in it.** This was not an undocumented
area, and the task is smaller than its title suggests. Every tree states the build-before-plan
requirement in its own `README.md`. Every tree's `HOW-TO-DEPLOY.md` covers its own build step.
`terraform-aws/src/README.md` goes into handler-level detail. The Azure and GCP `build.sh` headers
each already carry a section explaining how that script differs from the others and why.

Two gaps survived all of that:

- **No cross-cloud page.** `infra/MODULES.md` is the catalog for exactly this kind of question —
  it already carries an Overview table, a Module Comparison Matrix, and per-cloud notes — and it
  said nothing about packaging at all. Someone comparing the three trees had to open three shell
  scripts and assemble the comparison themselves.
- **AWS's `build.sh` pointed nowhere.** Azure's header explains how it differs from AWS and GCP;
  GCP's explains how it differs from AWS. AWS's explained only its own choice. The divergence was
  therefore discoverable from two of three directions, and the direction it was invisible from is
  the tree with the most documentation and the likeliest entry point for a reader.

**The divergence itself.** One rule generates all of it: *whoever installs the packages must be
the same thing that runs them.*

- **AWS vendors**, because a Lambda zip is the final artifact — Lambda does not build it, so
  whatever is not inside the zip does not exist at runtime. Wheels are resolved with an explicit
  `--platform manylinux2014_x86_64 --python-version 3.12 --only-binary=:all:` for the Lambda
  runtime rather than for the build machine.
- **Azure and GCP must not vendor**, because their zips are source rather than artifact. Oryx
  (via `SCM_DO_BUILD_DURING_DEPLOYMENT` and `ENABLE_ORYX_BUILD`) and Cloud Build respectively
  install `requirements.txt` against the real runtime image. Vendoring locally would push a
  developer machine's binaries into a Linux build.

The visible consequence, and what the new section leads with: the same `reason` handler ships as
**4.2 MB on AWS and 20 KB on Azure**, and neither number is a mistake. The cost of the split falls
on Azure and GCP, where an undeclared import is not caught by the build at all — it surfaces at
cold start, on a deployment that reported success. That is why both of those scripts treat a
missing `requirements.txt` as fatal, and why all six of GCP's packages carry one where AWS needs
exactly one.

**Action.**

1. Add a `## Handler Packaging` section to `infra/MODULES.md`, between the Module Comparison
   Matrix and the Dependency Graph — a nine-row comparison table plus the reasoning above.
2. Add the missing cross-reference block to `terraform-aws/src/build.sh`, matching the sections
   Azure's and GCP's already carry.
3. Point all three scripts at `MODULES.md`, so the comparison is reachable from whichever tree a
   reader opens first.

**Deliberately not done.** No new `src/README.md` for Azure or GCP. AWS has one because it
documents that tree's handlers, stubs, and environment variables — per-cloud content rather than
divergence — and writing two more of those is a separate task, not this one. Recording it here so
the asymmetry is a known choice rather than an oversight the next reader has to rediscover.

**Verify.**

That the documented sizes are real rather than copied from a stale build:

```bash
for t in aws azure gcp; do (cd "infra/terraform-$t/src" && ./build.sh); done
```

`reason.zip` should print `4.2M` for AWS, `20K` for Azure, `16K` for GCP. Only AWS's needs
network — it is the one that pip-installs.

That the divergence is reachable from every entry point, which was the actual gap:

```bash
grep -l "MODULES.md" infra/terraform-*/src/build.sh      # expect all three
grep -c "How this differs" infra/terraform-*/src/build.sh # expect 1 for each
```

---

### Task 11 — Add SAST scanning to CI

**Goal.** Have something read this repository's Python and its workflows for security defects,
rather than only checking that they parse.

**What was missing.** Nothing scanned code for vulnerabilities. The `examples` job runs
`compileall`, which parses without importing and so catches a syntax error and nothing else, and
the `secret-scan` job looks for committed credentials, which is a different question entirely.
Between them the repository had no check that would notice an injection, an unsafe
deserialisation, or a workflow handing a fork's code a writable token.

That last one is the sharp edge. `SECURITY.md` names "this repository's supply chain — the
workflows and scripts under `.github/`" as in scope, and until this task nothing tested that
claim in either direction. The policy was making a promise CI could not keep — the same failure
mode task 9 found in the scope lists, one directory over.

**Why CodeQL.** The constraint that decides it is already written in `checks.yml`'s header:
everything runs without cloud credentials, because a check that needs a secret is a check that
gets switched off the first time one expires. CodeQL is GitHub-native and free on public
repositories, so it needs no account, no token, and no third-party service that can start
charging or disappear. Semgrep and Checkov each mean a `pip install` in CI; that is not
disqualifying, but neither buys anything here that CodeQL does not already cover for Python.

The `actions` language is why this is two analyses rather than one. It reads the workflow files
themselves, catching expression injection through `${{ }}` interpolated into a `run` block and
the `pull_request_target`-plus-checkout pattern. Those are the vulnerabilities a public
repository taking pull requests actually has, and they live in exactly the files `SECURITY.md`
had already claimed were in scope.

**Why a separate workflow file.** CodeQL uploads to the code-scanning API, which needs
`security-events: write`. Top-level `permissions` are inherited by every job in a file, so
putting this in `checks.yml` would grant write access to the security tab to nine unrelated jobs
— including the one that downloads a binary over the network and runs it against the whole
repository. A separate file keeps the grant at job level where it belongs.

The schedule is the second reason. CodeQL is the only check here whose value includes "the
queries GitHub shipped this month still find nothing in code nobody has touched since August",
and a push trigger cannot answer that, because the finding arrives with the query rather than
with the commit. `gitleaks` re-reads the same history every run and gains nothing from a timer,
which is why it stays in `checks.yml`.

**The gap this does not close, stated because the task title hides it.** CodeQL has no Terraform
or HCL analyzer. By volume roughly half of this repository is `infra/` across four cloud/data-platform
trees, and none of it is scanned by this workflow. What guards those trees is the write-boundary suite,
which asserts exactly three properties by reading `.tf` files as text — it is not a general IaC
scan and does not become one because this task is marked `Done`. A reader who takes "SAST
scanning: Done" to mean the Terraform is covered has been misled by this table. Closing that gap
needs Checkov, tfsec, or `trivy config`, and belongs beside task 15 rather than folded in here.

**Action.**

1. Add `.github/workflows/codeql.yml` with a two-entry matrix — `python` and `actions`, both
   `build-mode: none`, `fail-fast: false` so one language's extraction error cannot discard the
   other's result.
2. Grant `security-events: write` at job level only; leave the workflow default at
   `contents: read`.
3. Trigger on push and pull request against `examples/`, `tests/`, `.github/scripts/` and
   `.github/workflows/`, plus a weekly cron.
4. Use the `security-extended` query suite rather than the default. The default is tuned to stay
   quiet in large production codebases, where a false positive costs a team an afternoon. This
   tree is small and mostly stdlib, so the extra queries have little surface to be noisy against,
   and the repository's whole subject is which patterns are safe to copy. If it does turn noisy,
   drop back to `security` — do not switch the workflow off.

**Verify.**

Structure, locally. Deliberately stdlib-only: `pyyaml` is not installed by any of this
repository's Python paths, and a Verify block that needs a dependency nobody has is the defect
tasks 2, 3 and 5 each shipped in turn.

```bash
pre-commit run check-yaml --files .github/workflows/codeql.yml

python3 - << 'PY'
src = open('.github/workflows/codeql.yml').read()
assert '\npermissions:\n  contents: read\n' in src, 'workflow-level permissions widened'
assert '      security-events: write' in src, 'missing job-level code-scanning grant'
assert '- language: python' in src and '- language: actions' in src, 'matrix incomplete'
assert 'queries: security-extended' in src, 'query suite not set'
assert 'schedule:' in src and 'cron:' in src, 'no weekly trigger'
print('ok')
PY
```

That the analysis actually ran, after the first push to `main`. This half matters more than it
looks: in the security tab, "scanned and found nothing" and "never uploaded" render identically.

```bash
gh api repos/somesh-ghaturle/Agentic-AI-Systems/code-scanning/analyses \
  --jq '[.[] | {category, created_at, results_count}] | .[0:4]'
```

Two categories should appear, `/language:python` and `/language:actions`. One category means the
matrix half-failed silently; `no analysis found` means nothing uploaded at all, which is the case
this second check exists to tell apart from a clean scan.

---

### Task 14 — Add `envs/staging`

**Goal.** A canary environment between dev and prod — one that catches, cheaply, the class
of failure that otherwise gets its first exercise during a production apply.

**The task as originally written did not describe this repository.** It called for copying
`envs/dev`, reducing Lambda memory to 512 MB and "Step Functions concurrency" to 10. Three
problems with that, all found by reading the trees rather than the plan:

- **There is no Step Functions concurrency setting.** The only concurrency control in the
  AWS tree is `reserved_concurrency` on write tools, and it is already 5 in *both* dev and
  prod. Nothing to reduce.
- **512 MB contradicts a documented decision.** `envs/dev` sets the `reason` function to
  1024 MB deliberately — it is the one package that vendors a dependency, and cold-start
  import time scales with memory. Halving it in staging would make cold starts slower there
  than in either neighbour.
- **Scale is not what separates dev from prod here.** Diff the two roots in any tree and the
  differences are posture: a public knowledge collection versus VPC-only, execution payloads
  in logs versus not, PITR off versus on, shared storage keys enabled versus disabled, no
  purge protection versus 90 days. "Smaller-scale prod" describes none of it, and a staging
  built to the letter of the plan would exercise nothing dev does not already exercise.

**What was built instead.** One rule, applied in all three trees:

> Staging takes every one of prod's **reversible** controls, and none of its
> **irreversible** ones.

The first half is what makes staging worth running: those settings are where a first prod
apply actually fails. The second half is what keeps it worth running — an environment that
inherits prod's one-way doors cannot be destroyed and rebuilt, and a staging environment
that is not rebuilt regularly stops resembling anything.

| | Taken from prod (reversible) | Taken from dev (irreversible or pure durability) |
| --- | --- | --- |
| **AWS** | VPC-only collection, `log_execution_data = false`, PITR on, alarm topic required, trace emitter required, prod's step budgets | Object Lock never (hard-coded `null`, not a variable), 7-day KMS window, 30-day retention, archive expires at 90 days |
| **Azure** | EP1 plans, storage shared keys off, Service Bus local auth off, private search endpoint, schema threshold 0, prod's step budgets | Vault purge protection off, no WORM lock, Cosmos continuous backup off, LRS not ZRS/GRS |
| **GCP** | Vertex floor setting on **and blocking**, `LOG_ERRORS_ONLY` call logging, prod's alert thresholds, Firestore PITR on, prod's budgets | No locked retention policy, delete protection off, SOFTWARE not HSM keys, 1 replica not 2 |

**Three settings are load-bearing and worth naming.** Each is a silent failure that only a
real environment can surface:

- **Azure EP1.** Y1 (Consumption) cannot join a VNet, so on a Consumption plan every private
  endpoint in the stack is unreachable. Rehearsing on Y1 would prove nothing about whether
  prod can reach its own search service. This is the largest cost line in the Azure staging
  environment and it is not optional — `function_service_plan_sku` exists so the trade is
  visible, not so it is taken lightly.
- **GCP's floor setting.** It is enforced by Vertex AI on every `generateContent` in the
  project, so enabling it for the first time in prod means the first request it ever blocks
  is a real one. It also reaches every Vertex AI caller in the project, which is why the
  root documents that staging wants its own project.
- **A private endpoint with no DNS zone.** On Azure, the service name resolves to its public
  IP from inside the VNet: traffic leaves the network while every resource reports healthy.
  Nothing in `terraform plan` sees this, which is exactly why it needs an environment.

**Deliberately not exposed as variables.** `archive_object_lock_days` (AWS),
`immutability_period_days` / `lock_immutability_policy` (Azure), and `retention_days` /
`lock_retention_policy` (GCP) are all present in the prod roots and absent from staging. Each
would let a single `terraform.tfvars` line permanently strand the storage of the one
environment whose value depends on being destroyable — none of the three can be undone by
any principal, including the account owner. The modules receive hard-coded nulls, and each
`variables.tf` carries a comment saying why the variable is missing rather than leaving the
omission to be read as an oversight.

**A naming constraint this surfaced.** `staging` is three characters longer than `prod`, and
all three trees derive resource names from `<project>-<env>-...` against a hard platform
limit. The maximum project name is therefore *shorter* in staging than in prod — the
opposite of the usual direction, and a validation failure for anyone copying prod's tfvars:

| | prod allows | staging allows | Limit being hit |
| --- | --- | --- | --- |
| AWS | 16 chars | 13 chars | 32-char OpenSearch collection name |
| Azure | 10 chars | 7 chars | 24-char storage account name (hyphens stripped) |
| GCP | 10 chars | 7 chars | 30-char service account ID |

Each `variables.tf` states this in its validation error rather than letting the platform
reject a half-finished apply.

**Action.**

1. Add `envs/staging` to all three trees — same file set as that tree's `envs/prod`,
   including AWS's separate `state-machine.json.tftpl` (prod's step budgets, not dev's).
2. Add the three staging roots to the `validate` matrix in `checks.yml`.
3. Update the docs that enumerate environment roots: `README.md`,
   `terraform-aws/README.md`, `terraform-gcp/ARCHITECTURE.md`,
   `terraform-azure/ARCHITECTURE.md`.

**Verify.**

That the roots exist and CI covers them:

```bash
for cloud in aws azure gcp; do
  test -d "infra/terraform-$cloud/envs/staging" && echo "$cloud/staging: OK" || echo "$cloud/staging: MISSING"
done
grep -c "envs/staging" .github/workflows/checks.yml   # expect 3
```

That they validate, which is what CI will run:

```bash
for cloud in aws azure gcp; do
  terraform -chdir="infra/terraform-$cloud/envs/staging" init -backend=false -input=false -no-color >/dev/null
  terraform -chdir="infra/terraform-$cloud/envs/staging" validate -no-color
done
terraform fmt -recursive -check infra/
```

That staging is not a renamed dev — the check the original Verify block was missing, and the
one that would have passed for a wrong implementation:

```bash
# Prod's reversible controls are present.
grep -q "log_execution_data = false"  infra/terraform-aws/envs/staging/main.tf
grep -q "allow_public_access = false" infra/terraform-aws/envs/staging/main.tf
grep -q "storage_shared_access_key_enabled = false" infra/terraform-azure/envs/staging/main.tf
grep -q "create_floor_setting = true"  infra/terraform-gcp/envs/staging/main.tf
echo "posture: OK"

# Prod's irreversible ones are not.
grep -q "object_lock_retention_days = null" infra/terraform-aws/envs/staging/main.tf
grep -q "lock_immutability_policy = false"  infra/terraform-azure/envs/staging/main.tf
grep -q "lock_retention_policy = false"     infra/terraform-gcp/envs/staging/main.tf
echo "destroyable: OK"
```

**Not done, and not in scope.** No `terraform plan` against a real subscription — that needs
cloud credentials and is task 6's blocked decision, not this one. These roots validate; they
have never been applied, which is the same status every other root in this repository has.

---

### Task 18 — Document secrets rotation

**Goal.** Provide clear guidance for rotating sensitive credentials.

**Status: Done.** [`docs/SECRETS-ROTATION.md`](SECRETS-ROTATION.md), linked from the root README
and from [`security-checklist.md`](security-checklist.md).

**The original task definition was written against a tree that does not exist**, and following
it would have produced a harmful document. It is recorded here rather than deleted, because the
gap between it and what shipped is the useful part:

| The plan said | What is actually there |
| --- | --- |
| `modules/security/bedrock.tf` | Does not exist. AWS security is one `main.tf`; Bedrock authorizes by IAM, so there is no key. |
| `modules/approval/dynamodb.tf` | Does not exist. The table is in `modules/approval/main.tf`. |
| `modules/approval/cosmos.tf` | Does not exist. Same — Azure's container is in `main.tf`. |
| `modules/security/vertex.tf` | Does not exist. Vertex authenticates with the caller's service account. |
| `modules/approval/firestore.tf` | Does not exist. GCP's database is in `modules/approval/main.tf`. |
| `./scripts/rotate-*-secrets.sh` | There is no `scripts/` directory. All three were fiction. |
| `aws iam create-access-key`, then paste into a `default =` in HCL | The trees create **no** static credentials — no `aws_iam_access_key`, no `google_service_account_key`, no `azuread_application_password`. Writing a live key into an HCL default is what `gitleaks` exists to stop. |
| "Approval gate tokens: every 24 hours (auto-rotated by default)" | Nothing auto-rotates them. Claim lifetime lives in handler code this repository does not ship. |

**What shipped instead** documents the tree as built: the two data-at-rest keys that really do
rotate (AWS annual and automatic, GCP 90-day and configurable) and the fact that Azure has no
customer-managed key at all; the optional model-API-key secret that no environment turns on, and
the divergence that matters if you turn it on — on GCP the value never enters Terraform
state, on Azure it does; Azure's dev-only storage shared access keys; and the absence of any
cloud credential in CI.

**Stale claims found and fixed while verifying this**, because the new document could not be
consistent with them. All three `modules/approval/README.md` files claimed approval tokens
expired after 24 hours, "configurable via `var.approval_token_ttl_seconds`". That variable exists
in no module, the 24 hours was never true, and the rotation steps beneath it invented CLI
commands (`az durable-functions task-token get`, `aws stepfunctions get-task-token`) and an
`APPROVAL_TOKEN` environment variable found nowhere in the repository.

What is actually implemented, and what the three sections now say:

| | Behaviour |
| --- | --- |
| Pending approval | Never expires — the executor's conditional write accepts a `pending` record at any age |
| `executing` claim | Reclaimable after `STALE_CLAIM_SECONDS`, default 900, a liveness window for a dead executor |
| Exposed as a Terraform variable | GCP and Snowflake (`var.stale_claim_seconds`; Snowflake validates `>= 60`). AWS and Azure have no dedicated variable — it goes through the generic `executor.environment` / app-settings passthrough, defaulting to 900 when unset |

[`BUILDING-BLOCKS.md`](agentic-system-architecture/BUILDING-BLOCKS.md) already carried the
correct 15-minute figure — 900 seconds is fifteen minutes — so the number was never the problem;
it now also carries the distinction between a pending approval and an `executing` claim, which is
the part that was missing everywhere.

The `Token Lifetime and Rotation` headings were left in place while their contents were rewritten,
so task 4's Verify block — which greps for exactly that heading in all three READMEs — still
passes. Renaming them would have silently broken it.

**Verify.**

```bash
test -f docs/SECRETS-ROTATION.md && echo "doc exists"

# No static credentials anywhere in the trees — the claim the document is built on.
grep -rn 'aws_iam_access_key\|google_service_account_key\|azuread_application_password' \
  infra/terraform-*/ --include='*.tf' | grep -q . \
  && echo "FAIL: a static credential resource exists" || echo "OK: no static credentials"

# The variable the approval READMEs used to promise still does not exist, and no longer appears.
grep -rn 'approval_token_ttl_seconds' infra/ | grep -q . \
  && echo "FAIL: stale variable reference remains" || echo "OK: stale reference gone"

python3 .github/scripts/linkcheck.py .
```

---

### Task 19 — Add `HOW-TO-RECOVER.md` per cloud

**Goal.** Give operators a runbook for the failures that actually need recovering: Terraform's
own state, the execution-state store, and a stuck approval claim.

**Status: Done.** [`docs/HOW-TO-RECOVER.md`](HOW-TO-RECOVER.md), linked from the root README and
`QUICKSTART.md`.

**This task had no prior definition to correct — the table listed it and nothing else did.**
Every claim in the shipped document was pulled from the tree rather than assumed, the same
discipline [Task 18](#task-18--document-secrets-rotation) applied to secrets:

- Terraform's own state is **local in all four trees today**. AWS, Azure, and GCP each carry a
  commented `backend "s3"/"azurerm"/"gcs"` block in every `envs/*/main.tf`; Snowflake carries no
  such scaffold at all, commented or otherwise. `*.tfstate` is gitignored, so none of it is
  backed up outside the machine that last ran `apply`.
- Execution-state recovery differs by cloud in ways the module code states plainly once you read
  past the resource block: AWS DynamoDB PITR is off in dev, on in staging and prod; GCP Firestore
  PITR follows the same pattern; Snowflake Time Travel runs 1/7/30 days across dev/staging/prod.
- **Azure was the actual finding.** `azurerm_storage_table.execution_state` sits in the same
  storage account as the module's `soft_delete_retention_days` setting, and the two look related
  until you read what that setting configures: `blob_properties.delete_retention_policy` and
  `container_delete_retention_policy`, both Blob Storage soft delete. The variable's own
  description says "days a deleted **blob or container** remains recoverable" — Table Storage is
  a separate data plane, and nothing in the module turns on its soft delete. Azure's execution
  state has no configured recovery path in any environment, dev through prod, which is a strictly
  worse position than AWS or GCP in dev (at least PITR exists there, just switched off).
- Stuck approval claims reclaim differently per cloud, and the document reuses [Task 18](#task-18--document-secrets-rotation)'s
  verified split rather than re-deriving it: AWS and Azure read `STALE_CLAIM_SECONDS` from an
  environment variable with no backing Terraform variable; GCP and Snowflake expose
  `var.stale_claim_seconds` and wire it through at plan time. Snowflake's reclaim is a `WHERE`
  clause inside `CLAIM_APPROVAL`, not a background sweep — a stale claim isn't freed until
  something next calls the procedure, not the instant the window elapses.

The archive module was deliberately left out of the runbook rather than given a thin section.
Every tree's archive supports a lockable retention policy that is irreversible once enabled by
design — recovering from it would defeat the reason it exists. The document says so instead of
manufacturing a recovery procedure for something that is not supposed to have one.

**Verify.**

```bash
test -f docs/HOW-TO-RECOVER.md
grep -q "AWS" docs/HOW-TO-RECOVER.md && grep -q "Azure" docs/HOW-TO-RECOVER.md \
  && grep -q "^## GCP" docs/HOW-TO-RECOVER.md && grep -q "^## Snowflake" docs/HOW-TO-RECOVER.md
grep -q "STALE_CLAIM_SECONDS\|stale_claim_seconds" docs/HOW-TO-RECOVER.md
grep -q "force-unlock" docs/HOW-TO-RECOVER.md
python3 .github/scripts/linkcheck.py .
```

---

### Task 20 — Add `multi-agent-debate` example

**Goal.** Demonstrate multi-agent coordination patterns.

**Status: Done.** [`examples/multi-agent-debate/`](../examples/multi-agent-debate/README.md),
with [`tests/test_multi_agent_debate.py`](../tests/test_multi_agent_debate.py) — 28 tests.

**The task definition contradicted the repository's own architecture**, and building it as
written would have shipped an example arguing against the rest of the repo. The sketch had
three roles — proposer, reviewer, **approver** — with the approver returning
`APPROVED: {action}`.

An agent that approves an agent's proposal is not an authorization step; it is the same
untrusted output wearing a different hat. Every tree in `infra/` enforces the opposite in
Terraform: the executor role is deliberately never granted the approve capability, because a
machine role that can approve its own proposal collapses the gate into a formality. An
`ApproverAgent` in `examples/` would have been the canonical illustration of the mistake,
presented as the pattern.

Two smaller divergences from the tree, both convention rather than substance:

| The plan said | The convention |
|---|---|
| `test_multi_agent.py` inside the example directory | Suites live in `tests/test_<example>.py` at the repo root — `unittest discover -s tests` |
| `requirements.txt`: "Only stdlib (no external dependencies)" | Stdlib examples ship a `requirements.txt` that carries a comment explaining the absence, not an empty file. See [`DECISION-LOGS/0004`](DECISION-LOGS/0004-stdlib-only-examples.md) |

**What shipped instead** keeps the three roles and removes the authorization. The arbiter
judges whether the debate has finished and advances no position of its own; it cannot propose
and it cannot oppose. A `Verdict` carries the improved proposal plus the objections that were
never answered, and `requires_human_approval` is a read-only property that is always `True` —
a property rather than a field, so no call site can construct one that claims otherwise.

The protocol guarantees, each with a test class and each mutation-tested:

| Guarantee | Prevents |
|---|---|
| `Verdict` has no approval field | A debate being mistaken for an authorization |
| Budget exhaustion sets `converged=False` | Exhaustion reported as agreement |
| Unanswered objections become `dissent` | Consensus manufactured by dropping the objector |
| The transcript closes with the verdict | History rewritten once the outcome is known |
| ≥2 critics with distinct perspectives | One opinion sampled three times reading as corroboration |
| The arbiter may not propose or oppose | The debate ending when the proposer satisfies themself |

Participants are scripted rather than model-backed, matching `harness-agent`'s verifier and
`trace-eval`'s graders: a protocol's guarantees are properties of the protocol, so a model
behind the roles adds variance without adding coverage and would make the suite need a key.

**Verify.**
```bash
python3 -m unittest tests.test_multi_agent_debate -v
python3 examples/multi-agent-debate/agent.py          # the demo, three endings

# The example must not grow an approval path.
grep -rniE 'def approve|APPROVED:|auto_approve' examples/multi-agent-debate/ \
  && echo "FAIL: an approval path appeared" || echo "OK: no approval path"

python3 -m unittest tests.test_security_policy        # SECURITY.md names every example
python3 .github/scripts/linkcheck.py .
```

---

### Task 21 — Add `tool-discovery` example

**Goal.** Demonstrate tools loaded from a directory at runtime rather than hardcoded in a
module, and show the read/write split surviving being discovered instead of declared.

**Status: Done.** [`examples/tool-discovery/`](../examples/tool-discovery/README.md), with
[`tests/test_tool_discovery.py`](../tests/test_tool_discovery.py) — 11 tests.

**This task had no prior definition — the table listed it and nothing else did**, so the shape
came from what every other tool-owning example already established rather than from a sketch to
correct. `hermes-agent/hermes/tools.py` declares its tools in Python, in a module written by the
same person who wrote the router; this example asks what has to stay true once tools instead
arrive by being dropped into a directory, which is closer to how a plugin system or an MCP
server's tool list actually behaves.

`discover.py` scans `tools/`, imports each `.py` file, and reads a four-attribute contract off
the loaded module (`NAME`, `ACCESS`, `DESCRIPTION`, `run`) rather than importing a `Tool` class
from the loader and constructing one inside the discovered file. That is a deliberate choice,
not a simplification: a file loaded through `importlib.util.spec_from_file_location` and a file
imported the normal way can become two different module objects for the same path on disk, so
an `isinstance()` check against a class re-imported that way is not reliable. Reading plain
attributes off the module sidesteps the whole trap.

The read/write split itself reuses `hermes-agent`'s reasoning rather than re-deriving it: two
`ToolRegistry` instances, one per access level, each refusing at `register()` to hold a tool of
the other kind, so a `Toolbelt` built from the read registry never holds a reference to a write
tool in the first place. **Mutation tested**: collapsed both registries into one and made
`Toolbelt.call()` filter by `tool.access` at call time instead — the "filter over one list"
`hermes-agent/hermes/tools.py`'s own docstring warns against. 6 of the 11 tests went red,
`TestTheSplitIsStructural` entirely, because `Toolbelt`'s constructor caught the corrupted
registry before any call-time filter ran. Reverted after confirming it; see the example's
README for the full account.

**Added to `SECURITY.md`'s in-scope list, not the out-of-scope one.** The other minimal
reference examples added under this plan (`context-compaction`, `checkpoint-agent`,
`multi-agent-debate`) disclaim security entirely — they read local files, call a model, and
print. `tool-discovery` is narrower than `hermes-agent`'s claim (there is no approval flow to
route around) but it does claim a write tool discovered from `tools/` can never be called
through the `Toolbelt`, and a routing path that broke that claim would be exactly the kind of
report `SECURITY.md`'s in-scope section exists to receive — see `tests/test_security_policy.py`,
which checks every example is named somewhere on that page.

**Verify.**

```bash
python3 examples/tool-discovery/discover.py
python3 -m unittest tests.test_tool_discovery -v
python3 -m unittest tests.smoke.test_example_smoke -v   # runs discover.py as a subprocess
python3 -m unittest tests.test_security_policy           # SECURITY.md names every example
python3 .github/scripts/linkcheck.py .
```

---

### Task 8 — Add `checkpoint-agent` example

**Goal.** Demonstrate state persistence and crash recovery.

**Action.**
Create `examples/checkpoint-agent/` with:

- `README.md`: Explains checkpointing and resumption
- `agent.py`: Implements checkpointing logic
- `state.json`: Example checkpoint file
- `test_checkpoint.py`: Tests for persistence and idempotency

**Implementation:**

```python
# examples/checkpoint-agent/agent.py
import json
from pathlib import Path

class CheckpointAgent:
    CHECKPOINT_FILE = Path(__file__).parent / "state.json"

    def __init__(self):
        self.state = self._load_state()

    def _load_state(self) -> dict:
        if self.CHECKPOINT_FILE.exists():
            return json.loads(self.CHECKPOINT_FILE.read_text())
        return {"completed_actions": [], "current_step": 0}

    def _save_state(self):
        self.CHECKPOINT_FILE.write_text(json.dumps(self.state))

    def run(self, action: str) -> str:
        # Simulate work
        result = f"Executing: {action}"
        self.state["completed_actions"].append(action)
        self._save_state()
        return result

    def resume(self) -> list:
        """Resume from last checkpoint."""
        return self.state["completed_actions"]
```

**Verify.**

```bash
rm -f examples/checkpoint-agent/state.json   # the example is about first-run behaviour
python3 examples/checkpoint-agent/agent.py "deploy-model"
python3 -c "import sys; sys.path.insert(0, 'examples/checkpoint-agent'); from agent import CheckpointAgent; print(CheckpointAgent().resume())"
test -f examples/checkpoint-agent/state.json
python3 -m unittest tests.test_checkpoint_agent
```

Two corrections against the first draft of this block, both found by running it.

**There is no `checkpoint_agent` package.** The draft's
`from checkpoint_agent.agent import CheckpointAgent` raises `ModuleNotFoundError`. This example is
a single `agent.py`, matching `e2e-agent` and `context-compaction`; only the multi-file examples
(`hermes/`, `traceeval/`, `harness/`) have a package directory, and a 70-line demo does not need
one. Import it by putting the example directory on `sys.path`, as above.

**The example's tests were never run.** They shipped as
`examples/checkpoint-agent/test_checkpoint.py`, but the `examples` CI job runs
`unittest discover -s tests` and `compileall examples/` — so the suite was syntax-checked and
never executed. checkpoint-agent was the only example keeping tests outside `tests/`; they now
live in `tests/test_checkpoint_agent.py` like every other example's, and CI runs 7 of them.

**The draft's first command was `agent.py "action1"`, which demonstrated the opposite of the
example.** `state.json` had been committed holding eight actions left from a test run —
`action1` among them — so the command printed `Already completed: action1` and executed nothing.
A checkpoint file is a run artifact: it is now gitignored alongside `state.tmp`, the scratch file
the atomic write renames from, and the example regenerates it on first run. Keep the `rm -f` in
the Verify block so the check always exercises the cold-start path.

---

## Phase 3 — Documentation & Governance (Week 4-6: 2026-09-06 to 2026-09-20)

This phase focuses on **documentation completeness** and **governance improvements**.

### Task 24 — Update `graph-agent` for production

**Goal.** Bring `graph-agent` from a minimal reference to something whose central claim is
true as written.

**Status: Done.**

**This task had no definition.** Unlike every other task in this plan it existed only as a row
in the progress table — no Action, no Verify, nothing saying what "for production" meant. What
follows is the definition derived by reading the example, recorded so the next person does not
have to derive it again.

**The tempting change is the wrong one.** `classify()` decides read-or-write by matching
phrases, which is the wrong shape for the job, and "make the classifier robust" looks like the
obvious production fix. It is not, for two reasons. It already fails *closed* — questions are
checked first, and anything unmatched falls to `read`, so an unrecognised request cannot reach
the write branch. And the properly robust design is the one `hermes-agent` already
demonstrates: never infer intent from text, have the caller name a tool that is registered read
or write. That design has no conditional edge in it, and a graph example with no branch
demonstrates nothing. The classifier stays, documented as the weak point, with the better
answer named.

**The real gap was durability.** The module's stated benefit is that "an approval that takes a
day is the same code as one that takes a second" — the graph suspends at `interrupt()`, state
goes to a checkpointer, and resumption is `Command(resume=...)` against a thread id, "from a
different process, hours later."

`build()` hardcoded `InMemorySaver()`. The README told you to edit that line for a real
deployment, which meant the single thing standing between the demo and a durable approval gate
was a source edit no test could reach — and the claim about a day-long approval was false for
anyone who ran the example as shipped.

**What shipped:**

1. `build(checkpointer=None)` takes the checkpointer as an argument. The default stays
   in-memory, deliberately: a durable checkpointer that defaulted on would put approval state
   on disk without anyone asking, and the demo and suite should need no database.
2. `TestDurableInterrupt` — five tests asserting the property that actually matters: **a second
   graph, built separately over the same checkpointer, resumes a thread the first one
   suspended.** That is the closest honest proxy for a process restart that needs no database,
   and it fails if `build()` ignores what it was passed. One test covers the dangerous
   direction specifically — a refusal must not become an approval across the handoff.
3. `architecture.md`, which `build()`'s own docstring already claimed existed and which was
   the one structural thing this example lacked against the worked-example bar. Its topology
   diagram is emitted by `graph.get_graph().draw_mermaid()`, so it cannot drift from the code.

No new dependency. `langgraph-checkpoint-sqlite` and the Postgres saver are separate packages;
pinning one to make a point the injected argument already makes would be the wrong trade.

**Also corrected:** both `requirements.txt` and the README claimed this was "the only example
with a floor above 3.9". Task 20 added `multi-agent-debate`, which is also 3.10+, for the
unrelated reason of `dict | None` in annotations.

**Verify.**
```bash
python3 -m unittest tests.test_graph_agent -v      # 28 tests; topology ones skip without langgraph
test -f examples/graph-agent/architecture.md

# With langgraph installed, the durability tests must actually run rather than skip:
pip install -r examples/graph-agent/requirements.txt
python3 -m unittest tests.test_graph_agent -v 2>&1 | grep -c TestDurableInterrupt

# The seam must be real — ignoring the argument has to fail the suite:
#   build(...): checkpointer=checkpointer or InMemorySaver()  ->  checkpointer=InMemorySaver()
# expected: FAILED (failures=1, errors=2)

# The diagram is generated, not hand-written, so it cannot drift:
cd examples/graph-agent && python3 -c "
import graph_agent as ga
live={l.strip() for l in ga.build().get_graph().draw_mermaid().splitlines() if '-->' in l}
doc={l.strip() for l in open('architecture.md') if '-->' in l}
assert live <= doc, live - doc
print('diagram in sync')"
```

---

### Task 15 — Add Terraform policy-as-code (OPA)

> **Built 2026-08-24, with the action below corrected.** The task as written could not run.
> Every defect was confirmed against the tree before anything was built; they are recorded here
> because the same mistakes are easy to reintroduce.
>
> **1. The approval-gate policy checked a mechanism this repository does not use.** It required
> the IAM action `aws:dynamodb:ConditionCheckItem`. That string appears nowhere in
> `infra/terraform-aws/` — and it is not a valid action name (there is no `aws:` prefix). The
> tree grants only `GetItem`, `PutItem`, `UpdateItem`, and `Query`. As written the helper never
> matched, so the rule would have denied all four Lambdas. The real primitive is an
> `aws_lambda_permission` named `write_tool_from_approval` carrying a `precondition` on
> `approval_executor_arn != null` — the dual lock in
> [ADR 0001](DECISION-LOGS/0001-dual-lock-aws.md).
>
> **2. `res.iam_role.policy[...]` is not a traversal that exists.** An `aws_lambda_function` has
> `role = <arn>`, a string. Neither HCL2 nor plan JSON nests the role's policy under the
> function.
>
> **3. `input.resource.type` matches neither input format.** Confirmed by running the parser:
> conftest's hcl2 output is `input.resource.<type>.<name>`, and plan JSON is
> `input.resource_changes[]`. There is no shape in which that rego binds.
>
> **4. `deny[msg]` is OPA v0 syntax,** removed in OPA v1.0. conftest 0.62.0 embeds OPA 1.6.0
> and requires `deny contains msg if { ... }`.
>
> **5. `startswith(action, "*")` is the wrong wildcard test.** Over-permission looks like
> `"s3:*"` or exactly `"*"` — a suffix or an exact match, not a prefix.
>
> **6. `least_privilege.rego` duplicates work that already landed.** `.checkov.yaml` carries 45
> skips and *none* of them are IAM-wildcard checks, so checkov's IAM rules are all active today
> and already assert zero unskipped findings (task 8). A second scanner re-checking that is a
> second opinion nobody reads. It was dropped rather than written.
>
> **What was built instead.** One policy over a gap no existing tool covers: **declared but not
> wired** — a resource that exists, reads as a control, and has nothing referencing it. checkov
> evaluates one resource at a time and cannot ask the question; `infra/*/tests/` reason across
> resources but cover a different control. Both modules name this failure mode in their own
> comments. See [`infra/policies/README.md`](../infra/policies/README.md).
>
> **And it reads source, not plan output.** The conventional way to run OPA against Terraform is
> on `terraform show -json`, which needs `terraform plan`, which needs credentials — the exact
> reason task 6 is Blocked. `conftest --parser hcl2` reads source and needs none, so this task
> did not inherit that blocker. The cost is that policies see expressions rather than resolved
> values; the README states it.
>
> **A single `infra/policies/`, not one per tree.** The invariant is shared even though each
> cloud's primitive differs by design (ADR 0002). Three copied policy directories would drift.

**Goal.** Catch resources that disagree with each other — the class of defect the other two
Terraform scanners structurally cannot see.

**Action.** (As built. The original action is preserved in the correction note above.)

1. One shared policy directory, `infra/policies/`, containing:
   - `lib.rego` — accessors over conftest's hcl2 parse tree
   - `guardrail_wiring.rego` — three rules, one per cloud primitive
   - `guardrail_wiring_test.rego` — eight unit tests, both directions per rule
   - `README.md` — which scanner answers which question, and why source not plan output

2. The invariant, in one sentence per tree: a content filter that nothing references filters
   nothing.

   | Tree | Control | What wires it |
   | --- | --- | --- |
   | AWS | `aws_bedrock_guardrail` | an `aws_bedrock_guardrail_version` referencing it |
   | Azure | `azurerm_cognitive_account_rai_policy` | `azurerm_cognitive_deployment.rai_policy_name` |
   | GCP | `google_model_armor_template` | a `google_model_armor_floorsetting` |

3. A `conftest` job in `checks.yml`, conftest pinned to 0.62.0 with a SHA256 checksum, matching
   the tflint and gitleaks install pattern. `conftest verify` runs **before** the tree scan: a
   policy that cannot fail passes every tree it is pointed at, which is indistinguishable from
   a policy that holds.

**Verify.**

```bash
# The policies' own unit tests — 8 tests, both directions per rule.
conftest verify --policy infra/policies

# The policies against each tree — 3 rules, expect 0 failures.
for tree in infra/terraform-aws infra/terraform-azure infra/terraform-gcp; do
  find "$tree" -name '*.tf' -not -path '*/.terraform/*' -print0 \
    | xargs -0 conftest test --parser hcl2 --combine --policy infra/policies
done
```

Both were run before this task was marked Done, and the rules were confirmed to fire by
neutering one rule body and watching `conftest verify` go red.

---

### Task 16 — Add `DECISION-LOGS/` with ADRs

**Goal.** Document architectural decisions for future maintainers.

**Action.**
Create `docs/DECISION-LOGS/` with ADR files:

1. **`0001-dual-lock-aws.md`:**
   - Why AWS uses both IAM policy AND Lambda resource policy
   - Trade-offs vs. single-lock approaches
   - Decision date: 2026-XX-XX

2. **`0002-azure-openai-vs-claude.md`:**
   - Why Azure uses Azure OpenAI instead of Claude via catalog
   - Pros: `azurerm_cognitive_account_rai_policy` for content filtering
   - Cons: Model inconsistency across clouds

3. **`0003-gcp-firestore-over-spanner.md`:**
   - Why GCP uses Firestore instead of Spanner for state
   - Cost, scalability, and consistency trade-offs

4. **`0004-stdlib-only-examples.md`:**
   - Why most examples use only the Python standard library
   - Exception: Examples that demonstrate specific frameworks (LangChain, Ray)

**Verify.**

```bash
ls docs/DECISION-LOGS/ | wc -l  # Expect at least 4
grep -q "Status: Accepted" docs/DECISION-LOGS/*.md
```

---

### Task 25 — Add `MIGRATION-GUIDE.md`

**Goal.** Help users adapt these patterns to existing projects.

**Status: Done.** `docs/MIGRATION-GUIDE.md`.

**What the specified draft got right.** Unusually for this plan, most of its factual claims
survived checking: there are six building blocks, GCP does use Firestore for state and Vertex
for models, `modules/security/` exists in the AWS tree, and Azure's boundary is genuinely
thinner — `MODULES.md` and `CHOOSING-A-TREE.md` both say so, and `modules/entra-audit` exists
because of it.

**Three things it got wrong.**

- It linked to `docs/FAQ.md`, which is Task 39 and not written. The link check would have
  failed on merge.
- It offered three clouds. There are four trees.
- It told readers to open an issue with a `migration` label. The templates are
  `.github/ISSUE_TEMPLATE/{bug_report,feature_request,security}.md` and there is no such label.

**The larger problem was that it was generic.** "Over-engineering", "you can't improve what you
don't measure", "ignoring the write boundary" — advice that would read identically in any
repository, which is the kind of documentation people skim once and never return to. This
repository has something better available: a documented record of mistakes that were actually
made here, several of them still visible in the code with the evidence left in place.

So the pitfalls section names them, ranked by how often they bite:

1. **Gating the model rather than the tool** — the model was never the dangerous part.
2. **An approval that does not survive a restart** — Task 24's `InMemorySaver` finding. It
   looks like it works right until the day it matters.
3. **Inferring read-versus-write from request text** — `graph-agent`'s keyword list contained
   `"refund"`, so *"what is the refund policy"* drafted a refund for an order nobody mentioned.
   The failure runs toward the privileged path.
4. **Depending on something undeclared** — Task 26's `typing_extensions` finding, which passed
   CI for weeks because the CI environment happened to install it transitively.
5. **Reaching for multi-agent too early** — and when you do, `multi-agent-debate` shows that no
   debater holds the write capability; the executor role is never granted approve in any of the
   four trees.
6. **Over-trusting one cloud's defaults.**

Each is a thing that happened, with the artefact still in the tree to look at.

**Also covered, because both surprise people mid-migration:** `src/build.sh` must run before
`terraform plan`, since every module calls `filebase64sha256` on its package at plan time and a
tree with unbuilt packages cannot be planned; and secrets reach the trees differently, with one
putting a secret value in Terraform state — `SECRETS-ROTATION.md` says which.

**Verify.**
```bash
test -f docs/MIGRATION-GUIDE.md
python3 .github/scripts/linkcheck.py .        # every link, including the four tree references

# The claims that are cheap to check and would rot silently:
grep -c 'FAQ' docs/MIGRATION-GUIDE.md         # 0 — Task 39 is not written
python3 -m unittest discover -s infra/terraform-aws/tests   # the suite step 4 tells you to copy
```

---

### Task 31 — Update `THREAT-MODEL.md`

**Goal.** Keep the threat model current with the tree it describes.

**Status: Done.**

**This task had no definition** — it was a table row reading "Update `THREAT-MODEL.md`", with no
Action and no Verify. The gap that actually existed, found while writing task 25, gives it one:
**the document had zero mentions of Snowflake.** It modelled three clouds, said so throughout,
and a fourth tree had been deployed under it.

That is the worst kind of documentation gap in a security document. It was not wrong — every
sentence about AWS, Azure, and GCP still held — it was *silently incomplete*, and a reader had
no way to tell the difference between "Snowflake was considered and is equivalent" and
"Snowflake was not considered".

**Snowflake is not averaged into "the clouds", because it changes the answers.** Each adversary
now carries a fourth verdict, and two of them differ in ways worth stating:

- **A1 (compromised orchestrator): holds, and is the easiest to widen.** Snowflake RBAC is
  purely additive — *there is no deny primitive* — and role grants are transitive. One
  `GRANT ROLE executor TO ROLE <anything the orchestrator inherits>` hands over every write tool
  at once. So the §6 row that already separated the trees now separates them three ways: GCP is
  override-proof, AWS and Azure fail to a broad grant that *names the resource*, and Snowflake
  fails to one that **names neither party**.
- **A2 (prompt-injected model): equal, but the read gap is widest here.** The orchestrator role
  is granted exactly four things — submit a proposal, Cortex Search, the guarded `COMPLETE`
  wrapper, and the read tool procedures. Three are read paths into the warehouse the platform
  exists to hold.

**A3 is genuine parity.** Snowflake's conditional `UPDATE` guarded by `ARGUMENTS_FINGERPRINT`
plus `SQLROWCOUNT = 1` looks least like the other three and enforces exactly the same invariant.

**A4 gained four Snowflake mutations** that pass `terraform validate` and look correct: an extra
`snowflake_grant_account_role` edge (the module already creates a legitimate one, so another
looks like the same pattern), a procedure losing `EXECUTE AS OWNER`, `CLAIM_APPROVAL` dropping
its `SQLROWCOUNT` check, and `APPROVE` granted to a machine role. All four are caught by
`infra/terraform-snowflake/tests/`, which is the one suite that walks a graph rather than
checking a resource — because with transitive inheritance, no single resource is the answer.

**Two entries added to §7 (not defended)** and one to §8 (assumptions): `ACCOUNTADMIN` is
unbounded with no deny to fall back on, so the boundary is the *absence* of a grant and only the
test suite can assert it; approvals are polled rather than delivered, so "approved" and
"executing" sit further apart than in the trees that resume on a callback; and the tree can
prove it does not create an inbound edge to the orchestrator, but not that an operator did not
add one by hand.

**One claim was corrected while writing this.** A first draft said an injected model "reaches
Cortex Search and every read procedure" — true, but it omitted that the orchestrator holds
`COMPLETE_GUARDED` rather than raw `SNOWFLAKE.CORTEX_USER`. That distinction is a real control:
granting the raw role leaves the guarded wrapper in place, still looking like a control, while
making its use optional. The suite asserts the raw grant is *absent* rather than that the
wrapper exists, and the document now says so.

**Also updated:** the root README described the document as covering "the three clouds".

**Verify.**
```bash
# The document must not describe itself as covering three clouds.
grep -c 'three clouds' docs/THREAT-MODEL.md README.md      # 0 in both

# Every §6 verdict is backed by a suite that runs with no credentials.
for t in aws azure gcp snowflake; do
  python3 -m unittest discover -s infra/terraform-$t/tests
done

# The A3 primitive claimed for Snowflake.
grep -c SQLROWCOUNT infra/terraform-snowflake/modules/approval/main.tf

python3 .github/scripts/linkcheck.py .
```

---

### Task 39 — Add `FAQ.md`

**Goal.** Reduce repetitive questions and improve discoverability.

**Status: Done.** [`docs/FAQ.md`](FAQ.md), linked from `QUICKSTART.md`'s **Get Help** section as
this task required, and from the root README and `MIGRATION-GUIDE.md`.

**Following the draft would have reintroduced the fiction task 18 removed.** Its
troubleshooting section answered "approval tokens keep expiring" with "tokens expire after 24
hours by default; update `var.approval_token_ttl_seconds`". That variable exists in no module,
and the 24 hours was never true — it is precisely the claim task 18 deleted from all three
`modules/approval/README.md` files. Shipping it in an FAQ would have put it back in the one
document people reach for when confused.

The answer now states the real behaviour and says explicitly that the common belief is wrong,
because anyone asking the question has read the old claim somewhere.

**`APPROVAL_REQUIRED=false` does not exist either**, and the draft's first answer told readers
to set it. Worse than useless: someone follows the instruction, sees no error, and believes the
gate is off — or believes it *could* be turned off by configuration.

The honest answer is that there is no switch **because the boundary is structural**. The
handler is handed a `Toolbelt` built from the read registry, and the constructor raises
`WriteBoundaryViolation` on anything else. There is no branch to skip because there is no
handle to skip it with. The answer redirects to what people actually want: `--approve` for one
action, or registering a tool as read while developing it.

**One draft claim survived checking:** `tools.py` is real —
`examples/hermes-agent/hermes/tools.py`.

**A weaker answer was replaced.** The draft answered "what if the model calls a write tool
anyway" with "the orchestrator checks the approval gate before executing". That describes a
design where the model *can* name a write tool and something intercepts it. What is implemented
is stronger: write tools are not in the toolbelt, so there is no name that reaches one, and a
second check inside `call()` refuses one anyway — with a comment saying it is belt and braces.

**A precision error was found while verifying the claim table**, and it was wrong in three
documents at once. Task 18's table, and `BUILDING-BLOCKS.md` after it, said
`STALE_CLAIM_SECONDS` was "GCP only (`var.stale_claim_seconds`); AWS and Azure set it as a
handler env var". Checking every occurrence in the tree:

| Tree | Reality |
| --- | --- |
| GCP | Dedicated variable, wired to the env var |
| **Snowflake** | **Also a dedicated variable**, validated `>= 60`, set to 900 in all three envs |
| AWS | No dedicated variable — `executor.environment` passthrough, defaults to 900 |
| Azure | No dedicated variable — executor app settings, defaults to 900 |

"GCP only" was wrong, and "AWS and Azure set it" implied a wiring that does not exist — nothing
in either tree sets it, so unset means 900. Corrected in `FAQ.md`, `ENHANCEMENT-PLAN.md`, and
`BUILDING-BLOCKS.md`.

**Verify.**
```bash
test -f docs/FAQ.md && grep -c "^##" docs/FAQ.md    # 19 headings across 3 sections

# The two claims that must never come back:
grep -c 'APPROVAL_REQUIRED' docs/FAQ.md             # 1 — named only to say it does not exist
grep -rn 'approval_token_ttl' infra/ | wc -l        # 0

# The Get Help link this task was blocked on:
grep -c 'docs/FAQ.md' QUICKSTART.md                 # 1
python3 .github/scripts/linkcheck.py .
```

---

## Phase 4 — Advanced Features (Week 7-9: 2026-09-20 to 2026-10-18)

This phase focuses on **advanced functionality** and **future-proofing**.

### Task 26 — Add example dependency graph to CI

**Goal.** Prevent circular dependencies and catch missing dependencies.

**Status: Done.**

**The goal was right and the graph was the wrong one.** As specified, this task built a graph
whose edges ran from each example to the PyPI distributions it pins, then called
`nx.find_cycle` on it. Packages have no edges back out, so that graph is bipartite and a cycle
in it is not merely absent but unconstructible — the check could never have fired, and
`networkx` was pulled in to run it.

There is a graph here that can cycle, and it is the one between examples. `trace-eval`
evaluates `hermes-agent` by putting the sibling directory on `sys.path` and importing `hermes`
from it. That edge is real, it runs in one direction today, and nothing would have stopped
someone adding the return edge. Built over examples rather than over packages, cycle detection
is meaningful — and it is a depth-first search over thirteen nodes, so it needs no dependency.

**The missing-dependency half found a real defect on its first run.** `graph-agent` imported
`typing_extensions` while pinning only `langgraph`. Nothing in CI could see it: `compileall`
parses without importing, and the `example-deps` job installs langgraph, which drags
typing-extensions in transitively. The example would have kept passing here and started failing
for anyone who installed it from its own requirements file the moment langgraph's dependency
tree shifted.

The fix was not to pin it. The import sat in a `try: from typing import TypedDict / except
ImportError: from typing_extensions import TypedDict` fallback labelled "Python 3.9 and below",
which was dead twice over — `typing.TypedDict` has existed since 3.8, so the branch was
unreachable, and this example requires 3.10+ regardless because langgraph will not install
below it. The dead branch was the whole source of the undeclared dependency.

**What shipped:**

1. `.github/scripts/example_deps.py`. Standard library only, like every other check here.
   Parses imports with `ast` rather than a regex, which is what makes guarded imports
   visible — the typing_extensions finding was inside a `try`/`except`, and a line-oriented
   regex missed it.
2. `tests/test_example_deps.py` — 33 tests. Six mutations were used to confirm they bite:
   disabling underscore folding, emptying the alias table, disabling cycle detection, leaving
   extras unstripped, and narrowing the `ast` walk to top-level statements each fail the suite.
3. The step in `checks.yml`'s `examples` job, which is unfiltered, because the script is fast
   and needs nothing installed.

**Four false positives, all found by writing the naive version first:**

- **Local sibling modules.** `from harness import ...`, `from debate import ...`,
  `from build_index import ...` are files next to the importer, not packages.
- **Cross-example imports look identical to missing pins.** `from hermes import Tracer` names
  no distribution and no local file. It is an edge in the second graph, not a fault in the first.
- **Import name is not distribution name.** `import faiss` is satisfied by `faiss-cpu`. PEP 503
  normalisation covers most of the gap on its own, leaving an alias table short enough to stay
  correct.
- **Requirements syntax.** `uvicorn[standard]==0.52.3` declares `uvicorn`.

**The unused direction is reported, not enforced.** `uvicorn` is invoked from the Dockerfile
rather than imported, and `numpy` is pinned to constrain a transitive dependency that would
otherwise float. Both are deliberate, and a check that failed on them would be wrong.

**Also corrected:** the `examples` job described itself as running "nine of the twelve
examples". Tasks 8 and 20 brought the tree to thirteen examples and ten suites.

**Verify.**
```bash
python3 .github/scripts/example_deps.py examples    # exits 0, lists pins and inter-example edges
python3 -m unittest tests.test_example_deps -v      # 33 tests

# The check must actually fail on a missing pin — remove the langgraph line and confirm:
#   examples/graph-agent/requirements.txt  ->  (empty)
# expected: ERROR: imported but not pinned: graph-agent: langgraph

# And on a cycle. Neither of these can be asserted by reading the script.
```

---

### Task 27 — Add performance tests to CI

**Goal.** Ensure examples maintain acceptable latency and throughput.

**Status: Done.** `tests/performance/test_performance.py`.

**The specified draft was closer to workable than most in this plan.** `--quiet` really is a
hermes-agent flag, and the command it names exits 0. Three things still needed correcting:

- `p95 = sorted(times)[int(len(times) * 0.95)]` over ten samples indexes element 9 — the
  maximum, not the 95th percentile. It was also computed and then never asserted on.
- `graph_agent.py "test query"` passes an argument `main()` does not read, and the example
  `sys.exit`s when langgraph is absent, so `check=True` turned a missing optional dependency
  into a test error rather than a skip.
- Twenty subprocess spawns for two assertions.

**The thresholds were the real problem, in the opposite direction from the obvious one.**
Measured here, `hermes-agent` takes ~37ms and `graph-agent` ~354ms. The specified ceilings were
5s and 10s — 135x and 28x headroom — which reads like carelessness but is closer to right than
a tight bound would be, and the reasoning is worth writing down because the instinct is to
tighten it:

**A test asserting 40ms fails whenever the runner is busy, gets labelled flaky, and gets
deleted — and the deletion takes the real signal with it.** Loose ceilings survive, and they
still catch the regression that actually threatens these examples: *something started doing
I/O*. A DNS lookup plus a TCP connect costs tens to hundreds of milliseconds when it succeeds
and seconds when it does not. A stdlib-only example computing in memory does not drift from
37ms to 800ms by accident; it gets there because someone added a network call, a model client,
or an accidental O(n²). Twenty-times headroom catches that as well as tight bounds would, and
unlike tight bounds it is still there in six months.

So the ceilings are ~20x measured cost, and the docstring says why, so the next person does not
"fix" them.

**Interpreter startup is reported separately**, because it is a third of hermes-agent's wall
clock — a bare `python3 -c pass` costs ~13ms here. Without splitting it out, a third of the
budget belongs to CPython rather than to the example, and a Python version bump would move the
number more than any plausible code change.

**Median rather than mean**, over five samples rather than ten. One slow spawn on a contended
runner moves a five-sample mean far more than its median. The maximum is printed but never
asserted on, being the sample most contaminated by whatever else the runner was doing.

**The baselines are in the table so the ceilings can be audited** rather than taken on faith,
and `TestTheBaselinesAreHonest` fails if any ceiling drops below 10x its baseline — the tight
bound this task is specifically trying not to reintroduce. Both behaviours were confirmed by
breaking them: a 0.9s sleep injected into hermes-agent fails the ceiling, and a 50ms ceiling
fails the headroom check.

**Verify.**
```bash
python3 -m unittest tests.performance.test_performance -v

# The guard must fire on the regression it claims to catch. In examples/hermes-agent/agent.py:
#   import argparse  ->  import argparse
#                        import time as _t; _t.sleep(0.9)
# expected: FAILED — hermes-agent median ~968ms exceeds its 800ms ceiling

# And it must refuse a ceiling tight enough to be flaky. In CASES:
#   ("hermes-agent", [...], 37, 800, None)  ->  (..., 37, 50, None)
# expected: FAILED — ceiling 50ms is under 10x its 37ms baseline
```

---

### Task 28 — Add runtime smoke tests to CI

**Goal.** Catch runtime issues that static checks miss.

**Status: Done.** `tests/smoke/test_example_smoke.py`.

**The goal was worth doing and the specified test could not have worked.** Three independent
faults:

1. **`self.assertIn("usage" or "Agent" or example, ...)`.** `or` short-circuits on the first
   truthy operand, so the expression is the constant `"usage"`. It reads as three alternatives
   and is one.
2. **Half the entry points were wrong.** It ran `examples/<name>/agent.py` for six examples;
   `trace-eval` is `eval.py`, `graph-agent` is `graph_agent.py`, and `context-compaction` is
   `compact.py`.
3. **It probed with `--help`.** Two of thirteen examples use argparse. The rest ignore unknown
   flags and run their demo, so the `"usage"` assertion fails on them — and `checkpoint-agent`
   takes a positional action, so `--help` made it report `Executing: --help`.

**What shipped instead: run each example the way its README documents, and assert the exit
code it promises.** Simpler, and closer to what a user actually does.

**Exit codes turned out to be the interesting part.** `hermes-agent` exits **2** when it
reaches a write it has not been told to approve, which its README states — that is the write
boundary refusing. A smoke test demanding 0 everywhere would have recorded the repository's
central control as a failure. It appears three times in the table instead:

| Invocation | Expected |
|---|---|
| `agent.py "what is the refund policy"` | 0 — read path |
| `agent.py "restart the billing service"` | **2** — proposal, unapproved |
| `agent.py "restart the billing service" --approve` | 0 — approved and executed |

The difference between those three is the only runtime assertion in CI that the boundary holds
when the example is *run* rather than imported. Mutating hermes to return 0 instead of 2 fails
the suite.

**Why this is not redundant with what already ran.** `compileall` parses without importing.
The unit suites import modules rather than executing entry points, so a `__main__` block that
raises is invisible to them — and it is the first thing a user hits. `example-deps.yml` imports
entry modules but does not run them.

**Details that mattered:**

- **Timeouts.** An example waiting on input it will never receive hangs rather than fails, and
  a hung job burns the runner's timeout reporting nothing. Each subprocess gets a hard limit
  and `stdin=DEVNULL`.
- **State.** `checkpoint-agent` persists to `state.json` beside its own source by design. It is
  gitignored so a run does not dirty the tree, but it carries between runs — the suite
  snapshots and restores it, so running twice tests the same thing twice and a developer's
  local state is not collateral.
- **Coverage cannot drift silently.** `TestTheTableItself` fails if an example exists that is
  neither smoke-tested nor listed in `SKIPPED` with a reason, and if any documented entry point
  moves. Both were confirmed by breaking them.

**Wired into two workflows.** Discovery in `checks.yml` picks up `tests/smoke/` for the
stdlib-only examples. `graph-agent`'s case skips there and runs in `example-deps.yml`, the one
job where langgraph is installed.

**Also corrected:** QUICKSTART listed `checkpoint-agent` as `python3 agent.py`. It requires a
positional action and exits 1 without one — an error introduced when Task 20's row was added.

**Verify.**
```bash
python3 -m unittest tests.smoke.test_example_smoke -v

# The boundary assertion must be real. In examples/hermes-agent/agent.py:
#   return 2  ->  return 0
# expected: FAILED — hermes-agent exited 0, expected 2

# Coverage drift must fail, not pass quietly:
mkdir examples/phantom && python3 -m unittest tests.smoke.test_example_smoke
# expected: FAILED — neither smoke-tested nor listed in SKIPPED
rmdir examples/phantom
```

---

### Task 40 — Add evaluation as a service

**Goal.** Turn `trace-eval` into a reusable service for scoring agent traces.

**Action.**

1. Create `services/trace-eval-service/` (container layer) and `trace_eval_service/` (importable package):
   - `trace_eval_service/app.py`: FastAPI application exposing `/score` endpoint
   - `Dockerfile`: Container for the service
   - `requirements.txt`: Dependencies
   - `README.md`: Documentation

2. API design:

   ```python
   # trace_eval_service/app.py
   from fastapi import FastAPI
   from pydantic import BaseModel
   from traceeval import scoring

   app = FastAPI()

   class TraceRequest(BaseModel):
       trace: list
       expected_answer: str | None = None
       grading_criteria: dict | None = None

   class ScoreResponse(BaseModel):
       path_score: float
       answer_score: float
       passed: bool
       discrepancies: list

   @app.post("/score", response_model=ScoreResponse)
   async def score_trace(request: TraceRequest):
       path_score, discrepancies = scoring.score_trace_path(request.trace)
       answer_score = scoring.score_answer(request.trace, request.expected_answer)
       return ScoreResponse(
           path_score=path_score,
           answer_score=answer_score,
           passed=path_score >= 0.8 and answer_score >= 0.8,
           discrepancies=discrepancies
       )
   ```

3. Add `docker-compose.yml` for local development

**Verify.**

```bash
test -f trace_eval_service/app.py
python3 -c "from trace_eval_service.app import app; print('Import OK')"
```

---

## Phase 5 — Future Architecture (Week 10+: 2026-10-18 onwards)

This phase explores **longer-term architectural directions**.

### Task 41 — Add model routing to `hermes-agent`

**Goal.** Route requests to different models based on complexity, cost, or SLA.

**Action.**
Extend `examples/hermes-agent/hermes/router.py`:

```python
class ModelRouter:
    MODELS = {
        "simple": {"name": "claude-haiku-4-5", "max_tokens": 1000, "relative_cost": 0.5},
        "complex": {"name": "claude-opus-5", "max_tokens": 4000, "relative_cost": 2.5},
        "code": {"name": "claude-sonnet-5", "max_tokens": 4000, "relative_cost": 1.0},
    }

    def route(self, query: str, context: dict) -> str:
        complexity = self._assess_complexity(query, context)
        if complexity > 0.8:
            return self.MODELS["complex"]
        elif "code" in query.lower() or any(f.name.endswith(".py") for f in context.get("files", [])):
            return self.MODELS["code"]
        else:
            return self.MODELS["simple"]

    def _assess_complexity(self, query: str, context: dict) -> float:
        # Implement complexity assessment
        # Consider: query length, number of entities, technical terms
        return 0.5  # Placeholder
```

**Verify.**

```bash
grep -q "class ModelRouter" examples/hermes-agent/hermes/router.py
python3 -m unittest tests.test_hermes_agent -v
```

**Status (2026-09-01).** Done. `ModelRouter` now returns bounded simple, complex, and code
profiles using explainable local signals (request complexity, technical terms, entities, and
files). It performs no model or network call; callers remain responsible for enforcing the
returned token and cost limits.

---

### Task 42 — Add `memory-agent` example

**Goal.** Demonstrate long-term memory patterns for agents.

**Action.**
Create `examples/memory-agent/` with:

- Vector memory (FAISS-compatible, with a dependency-free fallback)
- Graph memory (NetworkX-compatible, with a dependency-free fallback)
- Time-based decay
- Session management

**Implementation:**

```python
# examples/memory-agent/memory.py
import faiss
import numpy as np
from datetime import datetime, timedelta

class VectorMemory:
    def __init__(self, embedding_dim=384):
        self.index = faiss.IndexFlatL2(embedding_dim)
        self.embeddings = []
        self.metadata = []

    def add(self, text: str, embedding: np.array, metadata: dict = None):
        self.embeddings.append(embedding)
        self.metadata.append(metadata or {})
        self.index.add(embedding.reshape(1, -1))

    def search(self, query_embedding: np.array, k=3) -> list:
        distances, indices = self.index.search(query_embedding.reshape(1, -1), k)
        return [self.metadata[i] for i in indices[0]]

class TimeDecayMemory:
    def __init__(self, decay_rate=0.1):
        self.items = {}
        self.decay_rate = decay_rate

    def add(self, key: str, value: str):
        self.items[key] = {"value": value, "timestamp": datetime.now(), "weight": 1.0}

    def get(self, key: str) -> str | None:
        if key not in self.items:
            return None
        item = self.items[key]
        age = datetime.now() - item["timestamp"]
        item["weight"] = max(0, item["weight"] - self.decay_rate * age.total_seconds())
        if item["weight"] < 0.1:
            del self.items[key]
            return None
        return item["value"]
```

**Verify.**

```bash
test -f examples/memory-agent/memory.py
PYTHONPATH=examples/memory-agent python3 -c "from memory import VectorMemory, TimeDecayMemory; print('Import OK')"
python3 -m unittest tests.test_memory_agent -v
```

**Status (2026-09-01).** Done. The example uses dependency-free implementations with interfaces
that can be replaced by FAISS and NetworkX adapters, plus exponential decay and explicit session
scoping. It performs no persistence or network access by default.

---

### Task 43 — Hybrid cloud proof-of-concept

**Goal.** Demonstrate cross-cloud agentic systems.

**Action.**
Create `infra/terraform-hybrid/` with:

- Orchestrator on AWS (Step Functions)
- Tools on GCP (Cloud Functions)
- State on Azure (Cosmos DB)
- Knowledge on GCP (Vertex AI Vector Search)

**Architecture:**

```
infra/terraform-hybrid/
├── README.md
├── ARCHITECTURE.md
├── modules/
│   ├── aws-orchestrator/
│   ├── gcp-tools/
│   ├── azure-state/
│   └── gcp-knowledge/
└── envs/
    └── dev/
```

**Verify.**

```bash
test -d infra/terraform-hybrid/modules/aws-orchestrator
test -d infra/terraform-hybrid/modules/gcp-tools
test -d infra/terraform-hybrid/modules/azure-state
test -d infra/terraform-hybrid/modules/gcp-knowledge
terraform -chdir=infra/terraform-hybrid/envs/dev fmt -check
```

**Status (2026-09-01).** Done. The four provider-specific modules are wired by an opt-in dev
root. `enable_resources` defaults to `false`, and the POC passes resource IDs and endpoints
between modules without storing credentials or uploading data.

---

### Task 44 — Edge agents proof-of-concept

**Goal.** Deploy agents to edge/IoT devices.

**Action.**

1. Create `examples/edge-agent/` with:
   - Local-only execution (no cloud dependencies)
   - SQLite for state
   - Local approval gate (file-based)

2. Add Docker support for edge deployment

3. Document deployment to:
   - Raspberry Pi
   - NVIDIA Jetson
   - AWS IoT Greengrass

**Verify.**

```bash
test -f examples/edge-agent/agent.py
grep -q "sqlite\|SQLite" examples/edge-agent/*.py
test -f examples/edge-agent/Dockerfile
python3 -m unittest tests.test_edge_agent -v
```

**Status (2026-09-01).** Done. The edge agent uses local SQLite, exact single-use file approvals,
an in-memory default for safe demos, and an unprivileged Python container. Raspberry Pi, Jetson,
and Greengrass deployment notes are in its README.

---

### Task 45 — Human-in-the-loop UX dashboard

**Goal.** Add a web interface for approval workflows.

**Action.**
Create `examples/hermes-dashboard/` with:

- React frontend
- FastAPI backend
- Real-time updates via WebSockets
- Approval workflow UI

**Implementation:**

```
examples/hermes-dashboard/
├── backend/
│   ├── app.py
│   └── requirements.txt
├── frontend/
│   ├── package.json
│   └── src/
└── docker-compose.yml
```

**Verify.**

```bash
test -f examples/hermes-dashboard/backend/app.py
test -f examples/hermes-dashboard/frontend/package.json
python3 -m unittest tests.test_hermes_dashboard -v
```

**Status (2026-09-01).** Done. The dashboard displays exact proposal details and fingerprints,
records approve/reject decisions without executing tools, and broadcasts changes over WebSockets.
Its in-memory backend and local compose setup are intentionally development-only; authentication,
durable atomic storage, origin controls, and TLS are required before deployment.

---

## Phase 6 — Model Currency & Drift (2026-09-03 onwards)

Phase 6 came from a repository-wide review on 2026-09-03 rather than from the original plan.
Its subject is the class of decay this document had no task for: the repository pins model
identifiers in nine places across four Terraform trees and one example, and nothing in CI reads
any of them. The trees drifted apart silently, and one drifted far enough to stop working.

### Task 46 — Fix the GCP `reason` model/thinking mismatch

**Goal.** Make the GCP tree's pinned model and its API call agree, so the tree can run with its
own defaults.

**Status: Done.** [`infra/terraform-gcp/src/reason/main.py`](../infra/terraform-gcp/src/reason/main.py),
plus the three `envs/*/variables.tf` defaults, the three `terraform.tfvars.example` files, and
[`modules/model-integration/variables.tf`](../infra/terraform-gcp/modules/model-integration/variables.tf).

**The defect.** `DEFAULT_MODEL` was `claude-opus-4-5@20251101` while the call 110 lines below
sent `thinking={"type": "adaptive"}`. Adaptive thinking arrived with the 4.6 generation; Opus 4.5
takes the older `budget_tokens` form. The tree could not have served a request with the defaults
it shipped.

The comment above the call — "adaptive thinking is on by default for this model family" — is
true of the Opus 5 family and not of 4.5. The AWS handler carries the same call and the same
comment against `anthropic.claude-opus-5`, where both are correct. So this was not a design
disagreement between the trees: the call sites were modernised together and the GCP pin was left
behind.

**Why CI stayed green.** [`infra/terraform-gcp/src/tests/test_handlers.py`](../infra/terraform-gcp/src/tests/test_handlers.py)
stubs the `anthropic` module with a `SimpleNamespace`, so no test has ever evaluated the model
string against the parameters sent with it. A stub cannot reject an argument the real SDK would.
That gap is task 48's subject, not this one's.

**What the fix gives up, stated rather than absorbed.** The old comment argued for an
`@`-suffixed snapshot on reproducibility grounds: weights that move underneath a versioned prompt
make results non-reproducible. That argument was sound and the fix loses it — current-generation
Vertex models are addressed by the bare identifier, and `claude-opus-5` is not a frozen snapshot.
The trade was forced by the mismatch rather than chosen on its merits, and the replacement comment
says so. `PROMPT_VERSION` and the resolved model string on every trace remain the tie between a
result and what produced it.

Vertex supports adaptive thinking, `effort`, and structured outputs, so the rest of the call
needed no change. Region availability is still unvalidated by Terraform, which the `model_id`
description already says.

[ADR 0002](DECISION-LOGS/0002-azure-openai-vs-claude.md) quoted the old identifier as the Vertex
shape; its Context paragraph now quotes the new one and notes the change. The decision itself is
untouched — it turns on the Azure guardrail, not on which Claude the other trees call.

**Verify.**

```bash
grep -rn 'claude-opus-4-5' infra/                      # no hits
grep -n 'DEFAULT_MODEL' infra/terraform-gcp/src/reason/main.py
python3 -m unittest discover -s infra/terraform-gcp/src/tests   # 39 tests
python3 -m unittest discover -s infra/terraform-gcp/tests       # 11 tests
terraform fmt -check -recursive infra/
cd infra/terraform-gcp/envs/dev && terraform init -backend=false && terraform validate
```

---

### Task 47 — Complete the `e2e-agent` test dependency guard

**Goal.** Make [`tests/test_e2e_agent.py`](../tests/test_e2e_agent.py) skip when any dependency
it needs is absent, not only when the first one is.

**Status: Done.**

**The defect.** The guard tested `importlib.util.find_spec("fastapi")`. `app.py` imports four
third-party modules at module scope — `fastapi`, `pydantic`, `opentelemetry`, and
`opentelemetry.sdk`. In CI the distinction never showed: the `examples` job installs nothing and
skips, `example-deps` installs the pinned requirements and runs. A working tree holding `fastapi`
but not `opentelemetry` — the ordinary state after installing some other example's requirements —
passed the guard and then failed on the import, reporting a missing-`E2E_AGENT_API_KEY` assertion
for a missing package.

The suite's own docstring argues that a test passing for the wrong reason is worse than one that
does not run. Failing for the wrong reason is the same defect wearing the opposite sign, and it
is worse in one respect: it sends a reader looking for a security regression that is not there.

**Verified in both directions**, because a guard that skips everywhere would be a worse bug than
the one it replaced:

- Partial environment (`fastapi` present, `opentelemetry.sdk` absent): 3 skipped, and the skip
  message names the missing module rather than the package that was present.
- Complete environment (a venv built from `examples/e2e-agent/requirements.txt`): 3 run, 3 pass.

**Verify.**

```bash
python3 -m unittest tests.test_e2e_agent -v    # skips, naming the missing module

python3 -m venv /tmp/venv-e2e
/tmp/venv-e2e/bin/pip install -r examples/e2e-agent/requirements.txt
/tmp/venv-e2e/bin/python -m unittest tests.test_e2e_agent -v   # 3 run, 3 pass
```

---

### Task 48 — Audit model pins across the four trees

**Goal.** Give the repository one place that knows every model identifier it pins, and a check
that fails when they drift apart.

**Status: Done.** [`tests/test_model_pins.py`](../tests/test_model_pins.py) — 3 tests. Mutation
tested by reintroducing task 46's exact pin, which the allowlist rejects by name and file.

Writing it surfaced a limit worth recording: the first version scanned comments too, and failed
on the Snowflake tree the moment that tree explained *why* it does not use `claude-opus-5`. Full-
line comments are now excluded and Terraform `description` strings deliberately are not — a
description is contract surface a reader acts on, and task 46's stale identifier was sitting in
one. That distinction is the whole reason the check is worth having rather than a grep.

**The Snowflake question has an answer, and it is "hold".** Checked against Snowflake's model
availability documentation on 2026-09-03: Cortex *does* offer `claude-opus-5`, so the convenient
excuse — "Cortex has not shipped it" — is false. It offers it only through cross-region
inference, with no native region, while `claude-sonnet-4-5` runs natively. Cross-region inference
transmits the prompt and response out of the account's home region, is gated on an
ACCOUNTADMIN-only `CORTEX_ENABLED_CROSS_REGION`, and defaults to DISABLED on accounts created
before 2026-03-09. Bumping the default would hand every operator a tree that either fails on a
parameter they never set or works because their account already lets inference payloads leave
their region — a data-residency decision made for them, in a default, by a repository whose
subject is not making decisions like that for people. Recorded in the module with the condition
that reopens it: a native Cortex region for opus-5.

**Action.** The identifiers as of 2026-09-03, after task 46:

| Tree | Pinned | Assessment |
| ------ | -------- | ------------ |
| AWS | `anthropic.claude-opus-5` | Current |
| GCP | `claude-opus-5` | Current as of task 46 |
| Snowflake | `claude-sonnet-4-5` | Behind — but Cortex publishes its own catalog |
| Azure | `gpt-4o` | Deliberate, per ADR 0002 |

Snowflake is the open question and it is not answerable from this repository: `SNOWFLAKE.CORTEX.COMPLETE`
serves the models Snowflake chooses to offer, on Snowflake's schedule. Check their current catalog
before bumping, and record the answer either way — "Cortex does not offer it yet" is a finding
worth writing down, not a dead end.

Then add the check. A stdlib test that reads the pins out of the `.tf` files and asserts each is
on an allowlist this document maintains would have caught task 46 at the point it was introduced.
It must not call a network: the constraint that makes every other suite here safe to gate merges
on applies to this one too. The allowlist goes stale on its own schedule, which is the honest
version of the problem rather than a solution to it.

**Verify.** A test that fails when a pin leaves the allowlist, and passes on the current tree.

---

### Task 49 — Refresh `hermes-agent` router model profiles

**Goal.** Stop teaching cost routing with prices that no longer hold.

**Status: Done.** The second option was taken — ratios carry the lesson.
[`ModelProfile`](../examples/hermes-agent/hermes/router.py) now has `relative_cost`, a multiple
of the cheapest tier, and the lineup moves to `claude-haiku-4-5`, `claude-sonnet-5`, and
`claude-opus-5`.

The choice was between refreshing the figures and restructuring so they cannot rot. Refreshing
loses on its own terms: the example never calls a provider, so nothing in it ever contradicts a
stale number, and the same edit would be due again within the year. Only one ratio here is taken
from published pricing — Sonnet 5 to Opus 5, $2 and $5 per MTok on 2026-09-03, so 2.5x — and the
Haiku tier is placed below Sonnet to encode ordering rather than quote a rate. The comment says
so, because a number that looks like a price and is not is worse than no number.

`tests/test_hermes_agent.py` gains a test asserting `simple < code < complex`, which is what the
router is actually for. The cross-vendor mix in the old profiles turned out not to be a lesson —
neither the README nor the module docstring ever claimed multi-provider routing — so collapsing
to one vendor cost nothing. Task 41's listing above was updated to match; it is the same code.

**Action.** [`examples/hermes-agent/hermes/router.py:108-110`](../examples/hermes-agent/hermes/router.py)
hardcodes `gpt-4o-mini`, `gpt-4o`, and `claude-3-5-sonnet` with per-token costs. Nothing calls an
API, so nothing is broken — the example is a deterministic offline router and that is the point of
it. But its numbers are the lesson, and they are wrong now.

Two options, and the choice is worth making explicitly rather than defaulting into: refresh the
figures and accept that they decay again, or restructure the profiles so the *ratios* carry the
lesson and the absolute figures are visibly illustrative. The second survives contact with time;
the first is more concrete for a reader. `tests/test_hermes_agent.py` asserts on the names and
must move with whichever is chosen. `README.md:132` and this document's own task 41 listing quote the
same profiles.

**Verify.** `python3 -m unittest tests.test_hermes_agent -v`, and no stale figure left in the
example's README or this document.

---

### Task 50 — Revisit the `py39` floor

**Goal.** Decide whether the Python floor should still be 3.9.

**Status: Done.** The floor stays 3.9 and is now tested — the new `examples (3.9 floor)` job in
[`checks.yml`](../.github/workflows/checks.yml) runs the suite there.

**The framing in the Action below is what changed under examination.** It treats the choice as
"raise it or exercise it", and assumes raising is the modern answer. Two facts moved it the other
way. The examples genuinely run on 3.9 — verified, not assumed: the full suite passes on 3.9.6,
314 tests at the time, with every skip explained by an absent dependency or the one CI script
that needs 3.10+. And the alternative floors are worse than they look: 3.10 reaches end of life
in October 2026, so it buys a month, while 3.11 would drop users on distributions still shipping
3.9 to gain nothing any example here uses.

So the defect was never the floor. It was that nothing tested it — every job pinned 3.12, which
made "Python 3.9+" a claim the repository made about itself and never checked. That is the same
shape as task 5's secret-scan job running a removed subcommand and task 47's guard naming one of
four imports: a check that looks present and verifies nothing.

Making the job possible turned up three suites that **errored** rather than skipped without their
dependencies — `test_trace_eval_service`, `test_hermes_dashboard`, and `test_example_deps` — the
same defect task 47 fixed once in `test_e2e_agent`. Each is now guarded at the import, so the
3.9 job needs no exclusion list in the workflow; a list there would go stale silently, a guard
beside the import does not.

**And it exposed a bug in task 47's own fix.** That guard called
`importlib.util.find_spec("opentelemetry.sdk")`, which imports the parent package to look inside
it and therefore *raises* rather than returning None when `opentelemetry` is absent — crashing in
exactly the partial-install case the guard was written to catch. It passed CI because the job
that runs it installs the dependencies. Found only by running the suite somewhere they were
missing, which is an argument for the 3.9 job independent of the floor.

**Action.** Python 3.9 reached end of life in October 2025. [`pyproject.toml`](../pyproject.toml)
holds ruff at `target-version = "py39"`, and the reasoning there is careful and still internally
consistent: the floor is what keeps `UP` from rewriting nine examples into syntax their READMEs
promise they do not need. Raising it is therefore not a one-line change — it is a decision about
what the examples claim to run on, and the READMEs are part of the diff.

CI runs 3.12 throughout, so nothing here is tested on 3.9 anyway. That gap is itself an argument,
in either direction: either the floor is real and should be exercised, or it is not and should be
raised to something that is.

**Verify.** `ruff check .` clean at whatever floor is chosen, and every example README agreeing
with it.

---

### Task 51 — Re-evaluate ADR 0002 against Claude on Microsoft Foundry

**Goal.** Test the ADR against the condition it named for its own reopening.

**Status: Done.** Condition tested 2026-09-03 and **not met**; the decision stands. Recorded in
[ADR 0002](DECISION-LOGS/0002-azure-openai-vs-claude.md) under "Tested 2026-09-03".

Of the two halves, the first has been met and the second has not. Claude is a first-party
offering on Microsoft Foundry — Sonnet 4.5, Haiku 4.5, Opus 4.1 in public preview — so on the
Azure side vendor parity is now purchasable. But `azurerm` still cannot express the deployment:
a Claude deployment requires a `modelProviderData` property that is absent from the resource
specification the provider is generated from, so `azurerm_cognitive_deployment` cannot create one
at all. Tracked as hashicorp/terraform-provider-azurerm#31140, open since 2025-11-19 and still
open when checked.

The documented workaround is `azapi_resource` with `schema_validation_enabled = false`, or
creating the deployment in the portal and importing it. Those are precisely what alternative 1
rejected and what the Context section gives as the reason this tree exists. The content-filter
half is therefore moot rather than separately failed — `rai_policy_name` binds to an
`azurerm_cognitive_deployment`, and there is no such resource to bind to.

Re-test when #31140 closes. Nothing before that changes the answer, which is worth stating so the
next review is a one-line check rather than a repeat of this one.

**Action.** [ADR 0002](DECISION-LOGS/0002-azure-openai-vs-claude.md) closes with: "`azurerm`
gaining first-class coverage for a Claude catalog deployment *and* an attachable content filter
on it. At that point the divergence costs more than it buys and the tree should move, keeping the
same handler contract."

Claude is now a first-party offering on Microsoft Foundry, which is one half of that condition.
The `azurerm` half was not verifiable during the 2026-09-03 review — checking it needs the
provider schema, and the Azure tree was not initialised locally. So this task is "go check the
trigger you already wrote down", not "the trade has flipped".

Two questions decide it. Does `azurerm` carry a first-class resource for a Foundry Claude
deployment, or does it still need `azapi`? And can a content filter be bound to it in Terraform,
the way `rai_policy_name` binds one to `azurerm_cognitive_deployment`? Both must be yes. The
guardrail is the entire reason this tree is on Azure OpenAI, and the ADR's alternative 2 already
rejected giving it up.

If the answer is no, record that in the ADR with the date. An ADR whose reopen condition has been
tested and not met is stronger than one that has merely not been revisited.

**Verify.** Either an amended ADR recording the check and its date, or a migrated tree whose
handler contract is unchanged and whose filter is bound in Terraform.

---

### Task 52 — Add an MCP server example behind the write boundary

**Goal.** Show what a tool server looks like when its writes have to pass the same approval gate
as everything else in this repository.

**Status: Done.** [`examples/mcp-server/`](../examples/mcp-server/README.md), with
[`tests/test_mcp_server.py`](../tests/test_mcp_server.py) — 19 tests.

The organising idea is that discovery and authorization come apart. A client can list
`refund_order`, read its schema, and call it, and none of that is permission to run it. The write
tool is advertised rather than hidden on purpose: hiding it would be a weaker design that reads
as a stronger one, since a hidden tool is protected only by the client not guessing its name.

The claim is bound to the arguments, not the tool. `fingerprint()` hashes tool plus arguments
with `sort_keys=True`, so approving `refund_order` in the abstract is impossible — the test that
carries the point grants an approval for $10, calls with $4,000, and expects refusal. The token
is stripped before fingerprinting and before the call, or a caller could approve one action and
execute another by editing a field afterwards.

`tool-discovery`'s two-registry structure is restated rather than imported. `MCPServer` holds the
read and write registries as separate fields, so there is no "all tools" collection for a call to
resolve against and the unguarded branch can only ever see read tools. Restated because the
inter-example dependency graph is checked and kept shallow, and an example that reaches into a
sibling for its core mechanism stops being readable alone.

**Mutation tested twice.** Removing the `token is None` check turns 2 tests red; deleting the
access-level refusal in `ToolRegistry.register` turns 2 different ones red. Both reverted.

Stdlib only, so it stays in the dependency-free `examples` job. Named in `SECURITY.md`'s in-scope
list with its limits stated — the protocol subset is deliberately small, and a gap in MCP
conformance is a bug report rather than a vulnerability.

**Action.** MCP is defined in [`GLOSSARY.md`](agentic-coding-playbook/GLOSSARY.md), named
throughout the playbook, and listed in
[`infra/terraform-aws/checklists/pre-apply.md`](../infra/terraform-aws/checklists/pre-apply.md)
as something to vet like a CI plugin. No example implements one. The repository warns about
untrusted tool servers without showing what a trusted one looks like, which is the weaker half of
the lesson.

This is the most on-theme example missing. The repository's organising property is that a
state-changing action cannot reach production without a human approving that specific action; MCP
is the standard way tools now arrive from outside the codebase. The interesting question is
exactly the one this repo is built to answer: what has to stay true when the tool list is supplied
by a server you do not own.

[`examples/tool-discovery/`](../examples/tool-discovery/README.md) already did the neighbouring
work — its README notes that directory-loaded tools are "closer to how a plugin system or an MCP
server's tool list actually behaves" — so the read/write split and the two-registry structure
should be reused rather than re-derived.

Keep the dependency posture of the surrounding examples: if the protocol can be spoken over stdio
with the standard library, do that, and stay in the dependency-free `examples` CI job. Adding a
dependency moves it to `example-deps` and should be a decision, not a side effect.

**Verify.** A suite asserting a write tool advertised by the server cannot execute without an
approval claim, plus the mutation test the other example suites here carry — break the boundary
and confirm the suite goes red.

---

### Task 53 — Fix the red `lint` job

**Goal.** Get `ruff check .` passing again, at the version CI pins.

**Status: Done.** 11 findings across three files, from two unrelated commits — the diagram
tooling and the phase 9 budget-guard example. Six were autofixable; the rest were not.

`scripts/diagram-gif/embed.py` carried two `SIM115` (bare `open()`) and two `E501`. Moving the
file read and write to `pathlib` closed all four at once, which is why the fix is smaller than the
finding count suggests. `os.path.relpath` stayed: the generated link walks *up* out of the
document's directory, and `Path.relative_to` only learned that with `walk_up` in 3.12, above this
repository's floor.

`examples/budget-guard/agent.py` needed `RUF012` — `_HANDLERS` annotated `ClassVar`, matching the
`from typing import Callable, ClassVar` already used in `hermes/router.py` rather than inventing a
second convention. `Callable[..., None]` and not a spelled-out parameter list, because the call
site passes `quick` by keyword and a positional signature would misdescribe it.

The `RUF100` in `tests/test_budget_guard.py` is the one worth recording. It removed a
`# noqa: E402` — which is exactly what this file's own ruff configuration says should happen:
ruff's E402 exempts `sys.path` modifications outright, so the directive suppressed nothing. A new
one had drifted back in.

**Verify.** `uv tool run --from ruff==0.16.4 ruff check .` — clean.

---

### Task 54 — Fix the red `examples` job

**Goal.** Get `python3 -m unittest discover -s tests` passing.

**Status: Done.** Seven errors, all `AttributeError: module 'agent' has no attribute
'CheckpointAgent'`, and the cause is not in either file that reads as broken.

Three examples ship a file called `agent.py`. `test_budget_guard` and `test_checkpoint_agent` both
put their example directory on `sys.path` and then said `import agent`. Python caches by module
name, so whichever test module sorted first bound `sys.modules["agent"]` for the entire discovery
run and handed the other its module. Budget-guard sorts first; checkpoint-agent got budget-guard's
agent and failed on every test.

It went red when phase 9 added `budget-guard/agent.py`. Neither file changed; a third one arriving
was enough.

The fix reuses the idiom already in `tests/test_edge_agent.py`, which loads its example by path
under the name `edge_example` — and is precisely why that third `agent.py` was never affected.
Both colliding files now do the same. No shared helper: two call sites, and the pattern was
already in the tree.

**Verify.** Full discovery on both interpreters — 351 tests, `OK (skipped=21)` on 3.12 with
dependencies, `OK (skipped=62)` on the advertised 3.9 floor. The 62 is the number this plan
already documents for that job.

---

### Task 55 — Pin `hashicorp/setup-terraform` to a commit SHA

**Goal.** Clear the two open CodeQL `actions/unpinned-tag` alerts.

**Status: Done.** Both call sites in `checks.yml` — the `fmt` job and the `validate` job — moved
from `@v4` to `@dfe3c3f87815947d99a8997f908cb6525fc44e9e # v4.0.1`.

`setup-terraform` is the only third-party action in the repository; everything else is
`actions/*` or `github/*`, which ship immutable releases and are why CodeQL flags two steps rather
than thirty-four. A tag is mutable, so whoever controls it controls a step that runs before the
Terraform trees are read.

The SHA was confirmed twice from independent sources — the tags API and `git ls-remote` — both
resolving `v4` and `v4.0.1` to the same commit. The trailing version comment is not decoration:
without it the next person cannot tell what they are bumping, and the note in the file says to
move the comment with the SHA.

**Verify.** No `uses:` outside `actions/` and `github/` resolves to anything but a 40-character
SHA. All four workflow files still parse, 14 jobs intact.

---

### Task 56 — Harden the docs-preview markdown renderer

**Goal.** Stop `.github/scripts/docs_preview.py` from turning documentation into script execution.

**Status: Done.** Two defects, both in `render_inline`.

The escape ran with `quote=False` while the link rule dropped its second capture group into a
quoted `href`. A surviving double quote let a markdown link close the attribute and append its own
event handler. This was enough:

```text
[x](" onmouseover="alert(1))
```

Now `quote=True`. The payload is fenced above rather than inlined because `linkcheck.py` skips
fenced blocks and not code spans — written inline, it reads the attribute break as a relative link
and reports the document broken.

Second, nothing constrained the URL scheme, so `javascript:` and `data:` hrefs rendered live. The
new `safe_href` allows `http`, `https`, `mailto` and `tel` and rewrites everything else to `#`. It
tests a whitespace-stripped copy because browsers strip whitespace and control characters inside a
scheme before acting on it, which makes `java	script:` live; and it only treats a colon as a
scheme when it precedes any path separator, so a relative link like `docs/notes:draft.md` stays a
path.

**Verify.** `tests/test_docs_preview.py` — 4 tests covering the attribute break, the two dangerous
schemes, the obfuscated variant, and the relative path that must not be rewritten.

---

### Task 57 — Add `EVALUATION-ENGINEERING.md`

**Goal.** Give the feedback edge in the architecture overview its own chapter.

**Status: Done.** [`docs/agentic-system-architecture/EVALUATION-ENGINEERING.md`](agentic-system-architecture/EVALUATION-ENGINEERING.md).

The overview diagram calls trace-level evaluation the edge that "matters as much as the boxes",
and the folder had a dedicated chapter for context engineering and one for harness engineering
while evaluation was a section inside `BUILDING-BLOCKS.md`. Two runnable examples already carried
the argument — `trace-eval` and `eval-red-teaming` — so the material existed and had nowhere to be
read as a discipline.

The organising claim is the twin of harness engineering's. That chapter's is *the agent is not a
reliable narrator of its own progress*; this one's is *the answer is not a record of what
happened*. Harness engineering moves completion out of the model's reach; evaluation engineering
moves the verdict out of the output's reach. Both are "model proposes, code decides" applied to a
different decision.

Section 4 follows the same shape as harness engineering's fifth failure mode — a finding that came
out of running the example rather than reading a source. Mutation-testing `trace-eval`'s graders
surfaced a check that was present, correct, and had never been the reason anything failed, because
a boundary check always fired first on every case that should have exercised it. Generalised: a
check you have never seen fail is a check you do not know you have.

No external primary source, unlike the context and harness chapters. `REFERENCES.md` records that
honestly — four new rows, two marked as this document's framing and one as this repository's own.

**Verify.** `linkcheck.py` resolves every new relative link; the chapter is reachable from the
folder README's contents table and reading order, and cross-linked from both sibling chapters.

---

### Task 58 — Add `ENVIRONMENT-ENGINEERING.md`

**Goal.** Give a name and a chapter to the discipline the repository was already practising
across `infra/`, `budget-guard`, `checkpoint-agent`, and `HOW-TO-RECOVER.md`.

**Status: Done.** [`docs/agentic-system-architecture/ENVIRONMENT-ENGINEERING.md`](agentic-system-architecture/ENVIRONMENT-ENGINEERING.md).

The other chapters constrain the agent — what it sees, what it may conclude, how it is graded.
Each is allowed to assume its controls fire. This one starts where that assumption stops: you
cannot build an agent that never takes a wrong action, so the remaining variable is what a wrong
action costs, and that is a property of the environment rather than of the model.

The load-bearing claim is deliberately not a restatement of `BUILDING-BLOCKS` §6. Approval gates
decide *whether* an action happens; this chapter is about the price when one does not fire. Its
evidence is the tree's own: the comment atop the AWS write-boundary test, which records that the
"self-enforcing" boundary was true of the resource policy **and only of the resource policy**,
because Lambda grants same-account invocation if the identity policy allows it *or* the resource
policy does. Substituting `tool_arns_by_name` for `read_tool_arns` is a one-word edit that reads
as a simplification and opens the boundary while `terraform validate` still passes. Generalised:
a control with two enforcement points and one test has one enforcement point.

Section 3 argues that reversibility is a per-resource *direction* rather than a good to maximise,
and the counterexample is in this repository — every tree's `modules/archive` is deliberately
irreversible, because "evidence that can be fixed after the fact stops being evidence". Operational
state should fail toward recoverable and audit evidence toward immutable, and getting the
direction backwards is the actual failure.

Section 4 follows the shape the two previous chapters set, and takes task 6 as its subject. CI
runs `terraform validate` and never `plan`, because `plan` needs credentials and the no-secrets
constraint is worth more. That is the right trade *and* a fidelity gap — and the AWS boundary test
exists precisely because `validate` passes while the identity policy is wide open. Generalised:
every sandbox differs from production somewhere, and the difference is where your evidence stops.
Name the gap and write a separate check for each thing on the list.

Every quotation was verified against its source file rather than recalled — the AWS test comment,
both `HOW-TO-RECOVER.md` passages, the `budget-guard` step-versus-token contrast, and the
`checkpoint-agent` replay test's name.

**Verify.** `linkcheck.py` resolves every new relative link; the chapter is reachable from the
folder README's contents table and reading order, and cross-linked from the harness and
evaluation chapters. `REFERENCES.md` carries four new rows, two marked as this repository's own.

---

### Task 59 — Add the `second-path` example

**Goal.** Give [`ENVIRONMENT-ENGINEERING.md`](agentic-system-architecture/ENVIRONMENT-ENGINEERING.md)
§2 a runnable counterpart, the way every other chapter in that folder has one.

**Status: Done.** [`examples/second-path/`](../examples/second-path/README.md), with
[`tests/test_second_path.py`](../tests/test_second_path.py) — 16 tests.

The chapter's load-bearing claim was the only one in the set with no code behind it. `budget-guard`
covers caps checked before the effect, `checkpoint-agent` covers replay safety, and
`approval-gate-fuzzing` covers watching a gate refuse — but nothing ran the central argument, that
a control can be correct and simply not be on the path taken.

It is a small copy of the tree's own AWS finding rather than an invention. `READ_TOOLS` → `TOOLS`
in the `Orchestrator` constructor is `read_tool_arns` → `tool_arns_by_name` in about a hundred
lines of standard library: the gate is untouched and still correct, and a write executes with no
approval because the orchestrator never routes through it.

Distinct from [`tool-discovery`](../examples/tool-discovery/README.md), which argues two registries
beat a filter. That is about a check going the wrong way. This is about a second grant existing at
all, which is the failure mode where the check is right and irrelevant.

**The point is asserted, not described.** `TestTheGateIsNotEnough` opens the boundary, then runs
the entire gate suite programmatically and asserts it still passes — so "a green gate suite is not
evidence the boundary holds" is a test result rather than a sentence.

**Mutation tested, four breaks, all caught.** The third is the example restated: defaulting the
orchestrator to `TOOLS` turns 3 tests red while the gate suite alone still passes. The fourth found
a real gap — deleting the `claim is None` branch does not change whether the call is refused, since
`None` is not equal to the digest, so the first version of the suite passed with the branch gone.
What changes is the reason an operator is given. `Refused` exists to carry which control refused
and why, so the tests now assert the message rather than only the exception.

Stdlib only, so it stays in the dependency-free `examples` job. Named in `SECURITY.md`'s in-scope
list with the unusual shape stated plainly: the wide configuration is *supposed* to execute an
unapproved write and its tests assert that it does, so that path is the subject rather than a
vulnerability, while the same reachability in the default configuration would be a real bug.

**Verify.** `python3 -m unittest tests.test_second_path` — 16 tests. `python3 boundary.py` prints
the three-stage demonstration, ending with `reachable_writes` naming the tool the gate never saw.

---

### Task 60 — Cover harness and environment in the design review

**Goal.** Make [`checklists/design-review.md`](agentic-system-architecture/checklists/design-review.md)
cover the folder it reviews.

**Status: Done.** Two new sections, a strengthened evaluation section, and a reconciled priority
list.

The checklist had thirteen sections mapped to `BUILDING-BLOCKS` and `PRODUCTION-PRINCIPLES`, and
**no section for harness engineering or environment engineering** — zero mentions of harness,
environment, blast radius, or reversibility. Both chapters had existed for several tasks. So the
document that says "run this before you build, and again before you ship" silently skipped half
the disciplines the folder documents, which is precisely the failure this plan keeps naming: a
check that looks authoritative and verifies nothing.

Each chapter already ended in a checklist, so the material was written; it needed folding in. The
evaluation section also predated `EVALUATION-ENGINEERING.md` and covered only the
`BUILDING-BLOCKS` §5 material, so it gained the newer items — a check that reads events, graders
not sharing information, severity design, every check firing alone, version provenance.

**"The ten that matter most" became twelve**, and says so in the document rather than quietly
renumbering. The two additions are the load-bearing claims of the two missing chapters: paths to
a write effect that nobody enumerated, and completion nobody verified. Item 9 absorbed the
trace-level requirement instead of becoming a thirteenth, because an eval suite that never reads
a trace is not a separate problem from having no eval suite.

**Verify.** All four chapters are now referenced from the checklist; 103 checkbox items across 15
sections.

---

### Task 61 — Rewrite `ROADMAP.md` against the current tree

**Goal.** Make the file a newcomer reads for direction describe the repository that exists.

**Status: Done.** Last substantive touch was 2026-09-01, before the diagram work, the four
architecture chapters, and tasks 46-59. It named none of the four chapters, described the main
remaining work as "mostly documentation, governance, and community-facing improvements", and its
status snapshot listed AWS, Azure and GCP while omitting Snowflake and the hybrid tree.

The rewrite states the organising property first, carries a status table with counts taken from
the tree rather than remembered, and pairs each chapter with its runnable counterpart — the thing
worth protecting, since a chapter with no example drifts into assertion and an example with no
chapter is a trick nobody can generalise from.

It also adds **"What is deliberately not here"**, so three absences read as decisions rather than
oversights: no IaC scanner, no `terraform plan` in CI, and no benchmark numbers.

**Verify.** Every count in the status table matches the tree; `linkcheck.py` resolves every link.

---

### Task 63 — Diagram the hybrid Terraform tree

**Goal.** Close the last diagram gap.

**Status: Done.** [`docs/diagrams/terraform-hybrid-architecture.html`](diagrams/terraform-hybrid-architecture.html),
its GIF, and the archify source beside the other 46.

`infra/terraform-hybrid/ARCHITECTURE.md` was the only architecture document in the repository
without a diagram, and unlike the others it had no mermaid block to convert — so the source was
authored directly as archify JSON rather than ported, and `embed.py` did not apply.

The diagram carries the document's actual claim rather than decorating it: one job per cloud, and
the dashed lower half is the write path this POC deliberately does not deploy. Showing the absent
path is the point — the document's own warning is that a production deployment must put writes
behind the same approval executor as `hermes-agent`, and a diagram showing only what is deployed
would quietly drop that.

Validation needed two repairs: `variant` is not a component property at `schema_version: 1`, and
the label on the write-path edge landed inside the orchestrator node until it was given explicit
coordinates in the gap below it.

**Verify.** 47 diagrams, 47 GIFs, 47 sources. No `ARCHITECTURE.md` or `architecture.md` in the
tree lacks an embedded diagram.

---

### Task 64 — Check documented counts against the tree

**Goal.** Stop the counts stated in prose from drifting away from the repository they describe.

**Status: Done.** [`.github/scripts/docs_counts.py`](../.github/scripts/docs_counts.py), wired
into the `docs` job beside `linkcheck.py`.

This is the second recurrence. Commit `a2faa35` was titled "Fix eight stale claims found in
full-repo sweep", and by this audit the README had drifted again: it described **twelve jobs**
when `checks.yml` had fourteen, and **twelve examples** when there were twenty-three — including
"nine of the twelve examples" have suites, when twenty of the twenty-three do. `CONTRIBUTING.md`
still said "six of twelve examples" carry an empty `requirements.txt`. Hand-fixing a number
resets the clock rather than stopping it, which is the argument every other script in
`.github/scripts/` makes about its own subject.

Seventeen claims are checked across `README.md`, `CONTRIBUTING.md`, and `ROADMAP.md`. Each is a
regex with one capture group around the number; digits, unit words, tens words and hyphenated
compounds up to ninety-nine are understood, because this repository writes small numbers as words
in prose and digits in tables.
A claim whose regex stops matching is a **failure, not a skip** — rewording the sentence is
exactly the moment the number needs looking at again.

Reading `checks.yml` is a narrow scan for keys at two spaces of indentation under `jobs:` rather
than a YAML parse, because PyYAML would be the only dependency in a directory that has none.

**It earned its place on the first run.** It failed immediately on `ROADMAP.md` claiming 46
diagrams when the tree had 47 — a number stale by one commit, mine, from adding the hybrid
diagram in task 63 and not updating the roadmap I had rewritten hours earlier.

A second pass extended it over the infrastructure claims, and found three more: the README said
`terraform validate` ran over **ten** environment roots when the matrix has thirteen, and that
tflint walked **thirty** modules and **ten** roots when it walks forty-four and fourteen. Those
three numbers differ on purpose — `validate` skips the hybrid POC, tflint does not — so the
guard tracks them separately rather than as one "trees" count.

**Verify.** `python3 .github/scripts/docs_counts.py .` — seventeen claims, all matching. Reverting
any one number reproduces a failure naming the file, line, claimed value, and actual value.

---

### Task 65 — State the VPC-only collection's reachability gap

**Goal.** Stop `allow_public_access = false` from reading as though retrieval works in the
environments that set it.

**Status: Done.** A note above the network policy in
[`infra/terraform-aws/modules/knowledge/main.tf`](../infra/terraform-aws/modules/knowledge/main.tf),
a paragraph in [`infra/terraform-aws/README.md`](../infra/terraform-aws/README.md), and
[`infra/terraform-aws/tests/test_knowledge_reachability.py`](../infra/terraform-aws/tests/test_knowledge_reachability.py)
— 2 tests.

Staging and prod lock the knowledge collection to its VPC endpoint and grant collection data
access to the retrieve tool's role. No Lambda in the tree declares a `vpc_config`, so that tool
has no route to the endpoint: a query fails at the network layer before the data policy is read.
Both halves are deliberate on their own — a corpus reachable from the internet is the worse
default, and public handlers authorized by identity is the recorded posture for a reference
deployment — but nothing said what they add up to.

The AWS README came closest and got it backwards: it said staging exists so that "the first apply
is a bad place to find out that a VPC-only collection is unreachable from the retrieve tool."
Staging has the identical shape, so it does not catch the problem, it relocates it. That clause
is gone.

**Two pointers were false and are now absent rather than redirected.** `.checkov.yaml` and
[`infra/CHOOSING-A-TREE.md`](../infra/CHOOSING-A-TREE.md) section 4 both sent a reader to
`ENTERPRISE-ADAPTATION.md` for the private-networking transition. That document is about team
practice — autonomy levels, cost attribution, config layering, rollout — and contains nothing
about VPCs. Writing the missing section there would have made the pointer true by putting
deployment topology in the wrong document, so both now say the transition is undocumented and
name what it involves.

**Mutation tested, both directions.** Adding a `vpc_config` to `modules/tools` fails the first
test; removing the note from the knowledge module fails the second. The pair is what matters —
the day the handlers move into the VPC, four documents stating the absence become wrong, and the
test names all four.

**Verify.** `python3 -m unittest discover -s infra/terraform-aws/tests` — 13 tests, 2 of them new.
`grep -rn "vpc_config" infra/terraform-aws/` still returns nothing, and
`python3 .github/scripts/docs_counts.py` matches with `plan_tasks` at 65.

---

### Task 66 — Correct the module chart and carry the reachability guard to Azure

**Goal.** Make section 4 of [`CHOOSING-A-TREE.md`](../infra/CHOOSING-A-TREE.md) describe the
trees that exist, and check whether task 65's gap has siblings.

**Status: Done.** Three corrections to that page, a caveat in
[`infra/terraform-azure/modules/knowledge/main.tf`](../infra/terraform-azure/modules/knowledge/main.tf),
and [`infra/terraform-azure/tests/test_knowledge_reachability.py`](../infra/terraform-azure/tests/test_knowledge_reachability.py)
— 2 tests.

**The chart said two things that were not true.** The `identity` row explained AWS's absence as
"computes role ARNs in `locals` because they are deterministic". What the AWS `locals` compute is
a state machine ARN and the approval executor's, labelled *cycle-breakers*; role ARNs come from
module outputs, which is the distributed-identity design the AWS README already describes. The
`networking` row called the Azure module "wired to exactly one thing". It also declares the
resource group every other Azure module consumes as `module.networking.resource_group_name` —
delete it and the tree goes with it.

**A page called "Choosing a tree" did not mention one of the trees.** `grep -ci hybrid` returned
zero. [`terraform-hybrid/`](../infra/terraform-hybrid/README.md) is four modules and one `envs/dev`
root with `enable_resources = false`, so it is correctly not a fifth option — but silence made it
invisible rather than out of scope. It now has a paragraph saying which it is. The totals row
likewise read as an inventory while covering thirty of forty-four modules, and now says so.

**The gap in task 65 has one sibling, not two.** Azure reaches it through a variable rather than
a hardcoded value: supplying `knowledge_private_dns_zone_ids` in prod or staging creates the
private endpoint *and* sets `public_network_access_enabled = false`, while no Function App in the
tree is VNet-integrated. The public route closes, no handler has a private one, and the trigger is
a step that reads like hardening — which is why this one is worse than the AWS shape it mirrors.

GCP needed nothing. It ships no private path and claims none: `public_endpoint_enabled = true` is
hardcoded in the index endpoint with the reason next to it, `ingress_settings` defaults to
`ALLOW_ALL` and its description already names the trap in changing it. Snowflake is the only tree
that ships an ingress control it actually uses — an IP allow-list on the service users, empty in
dev. Nothing to correct in either, so nothing was written to them.

**Mutation tested, both directions.** Adding `virtual_network_subnet_id` to a Function App fails
the first test; removing the caveat fails the second; decoupling the env root from the DNS zone
variable fails both.

**Verify.** `python3 -m unittest discover -s infra/terraform-azure/tests` — 5 tests, 2 of them
new. `grep -rn "virtual_network_subnet_id" infra/terraform-azure/` returns nothing, and
`grep -ci hybrid infra/CHOOSING-A-TREE.md` no longer returns zero.

---

### Task 67 — Fix the red `lint` job on `main`

**Goal.** Get `checks` green again after tasks 65 and 66 turned it red.

**Status: Done.** Four ruff findings in
[`infra/terraform-aws/tests/test_knowledge_reachability.py`](../infra/terraform-aws/tests/test_knowledge_reachability.py)
and [`infra/terraform-azure/tests/test_knowledge_reachability.py`](../infra/terraform-azure/tests/test_knowledge_reachability.py):
two `UP032` (`.format` calls that should be f-strings) and two `SIM115` (`open()` outside a
context manager).

This is the same failure as task 53 and it happened the same way. Both suites were run before
committing — `python3 -m unittest discover` on all four trees, twice, plus mutation tests — and
`ruff` was not, because the change read as documentation with two test files attached. The `lint`
job lints everything, `tests/` and `.github/scripts/` included, so "mostly docs" is not a category
CI recognises.

The `SIM115` fix is the more useful of the two. The Azure suite was calling
`strip_comments_preserving_lines(open(path).read())` inside a comprehension, leaking a file handle
per `.tf` file in the tree; it now has a small `read()` helper with a `with` block, which is what
the AWS suite already borrowed from its neighbour. The tree's own helper module does not export
one, and that asymmetry is why it was written inline the first time.

Both suites still pass and both mutation checks still fail as designed — the f-string arguments
are evaluated when the assertion runs, so a broken interpolation would fail every run rather than
only the failing one.

**Verify.** `ruff check .` — all checks passed, on the pinned `ruff==0.16.4` the workflow installs.
`python3 -m unittest discover -s infra/terraform-aws/tests` and the Azure equivalent — 13 and 5.

---

## Definition of Done

All tasks are considered complete when:

1. **Code is merged** to the `main` branch
2. **Tests pass** in CI
3. **Documentation is updated** (if applicable)
4. **Verification commands** in this document pass

Run the full verification:

```bash
# Documentation checks
python3 .github/scripts/linkcheck.py .

# All tests pass
python3 -m unittest discover -s tests -v 2>&1 | tail -5
python3 -m unittest discover -s examples/*/tests -v 2>&1 | tail -5

# Terraform checks
terraform fmt -check -recursive infra/
for d in infra/terraform-*/envs/*/; do
  terraform -chdir="$d" validate
done

# Example syntax
python3 -m py_compile examples/**/*.py

# Git status clean
git status --short
```

---

## Changelog

| Date | Change | Author |
| ------------ | ----------------------------------------------------------------------- | ----------------- |
| 2026-08-16 | Initial enhancement plan created with 45 tasks across 8 categories | somesh-ghaturle |
| 2026-08-16 | Reconciled progress table against working tree; 4 Done, 2 In Progress | somesh-ghaturle |
| 2026-08-16 | Completed tasks 2 and 35; fixed a terraform hook that skipped files | somesh-ghaturle |
| 2026-08-16 | Completed task 5 (pinned gitleaks, full history, allowlist); task 6 blocked | somesh-ghaturle |
| 2026-08-16 | Verified tasks 4 and 8; untracked checkpoint state artifact; task 3 label clash noted | somesh-ghaturle |
| 2026-08-18 | Completed task 9; classified 2 unlisted examples, added 9 disclaimers | somesh-ghaturle |
| 2026-08-19 | Task 3 resolved: deleted duplicate `GOOD-FIRST-ISSUE`, kept GitHub's default | somesh-ghaturle |
| 2026-08-22 | Completed task 11: CodeQL over Python and workflows; Terraform gap recorded | somesh-ghaturle |
| 2026-08-22 | Completed task 10: packaging divergence catalogued in `infra/MODULES.md` | somesh-ghaturle |
| 2026-09-03 | Added Phase 6 (tasks 46-52) from a model-currency review; completed 46 and 47 | somesh-ghaturle |
| 2026-09-06 | Added tasks 53-57: two red CI jobs, the CodeQL action pin, the docs-preview XSS fix, and the evaluation chapter | somesh-ghaturle |
| 2026-09-06 | Added task 58: the environment engineering chapter, completing the four-chapter set | somesh-ghaturle |
| 2026-09-06 | Added task 59: `second-path`, the runnable counterpart to the environment chapter | somesh-ghaturle |
| 2026-09-06 | Added tasks 60-63: closed four gaps between what the docs claim and what the tree does | somesh-ghaturle |
| 2026-09-06 | Added task 64: a CI check for documented counts, after the second recurrence of the same drift | somesh-ghaturle |
| 2026-09-07 | Added task 65: named the VPC-only collection's reachability gap and guarded it | somesh-ghaturle |
| 2026-09-07 | Added task 66: fixed two false notes in the module chart, added the missing fifth tree, guarded the Azure sibling | somesh-ghaturle |
| 2026-09-08 | Added task 67: fixed the red `lint` job the two guard suites introduced | somesh-ghaturle |

---

## Links

- [README.md](../README.md) — Repository overview
- [REPO-AUDIT.md](REPO-AUDIT.md) — Previous audit and remediation (fully resolved)
- [HARDENING-PLAN.md](HARDENING-PLAN.md) — CI hardening tasks
- [CONTRIBUTING.md](../CONTRIBUTING.md) — How to contribute
- [THREAT-MODEL.md](THREAT-MODEL.md) — Security threat model
