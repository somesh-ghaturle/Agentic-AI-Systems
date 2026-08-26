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
| 6 | Add `terraform plan` to CI | CI/CD | High | Blocked | | 2026-08-23 |
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
| 17 | Add cost monitoring module | Infrastructure | Medium | Not Started | | 2026-09-20 |
| 18 | Document secrets rotation | Infrastructure | Medium | Done | | 2026-09-06 |
| 19 | Add `HOW-TO-RECOVER.md` per cloud | Infrastructure | Medium | Not Started | | 2026-09-13 |
| 20 | Add `multi-agent-debate` example | Examples | Medium | Done | | 2026-09-06 |
| 21 | Add `tool-discovery` example | Examples | Medium | Not Started | | 2026-09-13 |
| 22 | Add `context-overflow` example | Examples | Medium | Not Started | | 2026-09-20 |
| 23 | Add `eval-red-teaming` example | Examples | Medium | Not Started | | 2026-09-27 |
| 24 | Update `graph-agent` for production | Examples | Medium | Done | | 2026-09-06 |
| 25 | Add `MIGRATION-GUIDE.md` | Documentation | Medium | Not Started | | 2026-09-13 |
| 26 | Add example dependency graph to CI | CI/CD | Medium | Done | | 2026-09-06 |
| 27 | Add performance tests to CI | CI/CD | Medium | Not Started | | 2026-09-20 |
| 28 | Add runtime smoke tests to CI | CI/CD | Medium | Not Started | | 2026-09-13 |
| 29 | Add `terraform plan` cost estimation | CI/CD | Medium | Not Started | | 2026-09-20 |
| 30 | Add approval gate fuzzing | Security | Medium | Not Started | | 2026-09-20 |
| 31 | Update `THREAT-MODEL.md` | Security | Medium | Not Started | | 2026-09-13 |
| 32 | Add `COMPLIANCE.md` | Documentation | Low | Not Started | | 2026-10-11 |
| 33 | Add discussion topics | Community | Low | Not Started | | 2026-10-04 |
| 34 | Add `ROADMAP.md` | Community | Low | Not Started | | 2026-09-13 |
| 35 | Add badges to README | Community | Low | Done | | 2026-10-11 |
| 36 | Add `CITATION.cff` | Community | Low | Not Started | | 2026-10-18 |
| 37 | Convert Mermaid diagrams to code | Documentation | Low | Not Started | | 2026-10-04 |
| 38 | Add automated docs preview | CI/CD | Low | Not Started | | 2026-10-04 |
| 39 | Add `FAQ.md` | Documentation | Medium | Not Started | | 2026-09-06 |
| 40 | Add evaluation as a service | Future | Medium | Not Started | | 2026-09-27 |
| 41 | Add model routing to `hermes-agent` | Future | Medium | Not Started | | 2026-10-04 |
| 42 | Add `memory-agent` example | Future | Medium | Not Started | | 2026-10-18 |
| 43 | Hybrid cloud proof-of-concept | Future | Low | Not Started | | 2026-11-01 |
| 44 | Edge agents proof-of-concept | Future | Low | Not Started | | 2026-11-15 |
| 45 | Human-in-the-loop UX dashboard | Future | Low | Not Started | | 2026-11-01 |

**Status verified 2026-08-16** by running each task's own **Verify** block against the working
tree, and kept current as tasks have landed since. Nineteen tasks now pass: 1, 2, 3, 4, 5, 7,
8, 9, 10, 11, 12, 13, 14, 15, 18, 20, 24, 26, and 35. Task 6 is `Blocked`. The remaining 25
verified as genuinely absent.

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
  to all three clouds. See the note in its section.
- **Task 22** — `examples/context-compaction` already exists. Confirm `context-overflow` is a
  distinct scenario rather than a second name for the same one.
- **Task 26** — `.github/workflows/example-deps.yml` already installs each example's pinned
  requirements in isolation and imports every entry module. The cycle detection is the only
  coverage `scripts/dependency_graph.py` adds; scope the task against what already runs.
- **Task 31** — has no detail section, and `docs/THREAT-MODEL.md` was written in the same batch as
  this plan. What the update should add is undefined.
- **Task 41** — `examples/hermes-agent/hermes/router.py` already exists, but it holds `Router`,
  which routes intents to approval and execution. That is not the `ModelRouter` this task's Verify
  greps for; model routing is a new class, not an edit to the existing one.

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

> **Blocked — needs a decision before any of the YAML below is worth writing.** The Verify block
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
or HCL analyzer. By volume roughly half of this repository is `infra/` across three clouds, and
none of it is scanned by this workflow. What guards those trees is the write-boundary suite,
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
| Exposed as a Terraform variable | GCP only (`var.stale_claim_seconds`); AWS and Azure set it as a handler env var |

[`BUILDING-BLOCKS.md`](agentic-system-architecture/BUILDING-BLOCKS.md) already carried the
correct 15-minute figure; it now also carries the distinction between a pending approval and an
`executing` claim, which is the part that was missing everywhere.

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

> **Blocked — needs a decision before any of the YAML below is worth writing.** The Verify block
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
or HCL analyzer. By volume roughly half of this repository is `infra/` across three clouds, and
none of it is scanned by this workflow. What guards those trees is the write-boundary suite,
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

**Two stale claims were found and fixed while verifying this**, because the new document could
not be consistent with them:

- All three `modules/approval/README.md` files claimed approval tokens were "configurable via
  `var.approval_token_ttl_seconds`". That variable exists in no module. The rotation steps under
  it invented CLI commands (`az durable-functions task-token get`, `aws stepfunctions
  get-task-token`) and an `APPROVAL_TOKEN` environment variable that appears nowhere in the
  repository. All three sections now say where claim lifetime actually lives. The section
  heading is unchanged, so task 4's Verify block still passes.
- [`BUILDING-BLOCKS.md`](agentic-system-architecture/BUILDING-BLOCKS.md) said the claim TTL
  "default is 15 minutes (configurable)", contradicting the READMEs' 24 hours and backed by
  nothing. It now reads as the recommendation it is.

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

**Action.**
Create `docs/MIGRATION-GUIDE.md` with:

```markdown
# Migration Guide: Adapting Agentic-AI-Systems Patterns

This guide helps you integrate the patterns from this repository into your existing
agentic AI projects.

## Step 1: Assess Your Current Architecture

Evaluate which of the [six building blocks](agentic-system-architecture/BUILDING-BLOCKS.md)
you already have:

- [ ] Model routing
- [ ] Tools (read/write split)
- [ ] Memory and state
- [ ] Orchestration
- [ ] Trace-level evaluation
- [ ] Approval gates

## Step 2: Choose Your Starting Point

### Option A: Greenfield Project
Start with the `starter-agent` and add building blocks incrementally.

### Option B: Existing Project
1. **Add the write boundary** (most critical):
   - Separate tools into read/write categories
   - Add approval gates for all write actions
   - Use `hermes-agent` as a reference

2. **Add trace-level evaluation**:
   - Instrument all actions with tracing
   - Use `trace-eval` as a reference

## Step 3: Cloud-Specific Guidance

### AWS
1. Deploy `infra/terraform-aws/envs/dev`
2. Gradually migrate existing resources into the modules
3. Use the IAM patterns from `modules/security/`

### Azure
1. Deploy `infra/terraform-azure/envs/dev`
2. Note: Azure has thinner write boundary enforcement (see THREAT-MODEL.md)
3. Add Entra audit alerts for additional protection

### GCP
1. Deploy `infra/terraform-gcp/envs/dev`
2. Use Firestore for state (best IAM deny policy support)
3. Use Vertex AI for model hosting

## Step 4: Testing Your Migration

1. **Write boundary tests**: Verify no write action can bypass approval
2. **Trace validation**: Ensure all actions are properly traced
3. **Failure testing**: Simulate crashes and verify recovery

## Common Pitfalls

1. **Over-engineering**: Start with a single-agent pipeline, not multi-agent
2. **Ignoring the write boundary**: This is the most critical security control
3. **Skipping trace-level evaluation**: You can't improve what you don't measure

## Support

If you encounter issues, please:
1. Check the [FAQ](FAQ.md)
2. Review the [THREAT-MODEL.md](THREAT-MODEL.md) for security considerations
3. Open a GitHub issue with the `migration` label
```

**Verify.**

```bash
test -f docs/MIGRATION-GUIDE.md && grep -c "building blocks\|write boundary\|trace" docs/MIGRATION-GUIDE.md
```

---

### Task 39 — Add `FAQ.md`

**Goal.** Reduce repetitive questions and improve discoverability.

> `QUICKSTART.md` shipped with a **Get Help** link to `docs/FAQ.md` before the file existed, which
> broke the `docs` CI job. The dead link was removed on 2026-08-16; restore it under **Get Help**
> as part of this task.

**Action.**
Create `docs/FAQ.md` with sections:

```markdown
# Frequently Asked Questions

## General

**Q: Can I disable the approval gate in development?**
A: Yes, but this is strongly discouraged. The approval gate is the primary security
control preventing unauthorized state changes. If you must disable it for local testing:
1. Set `APPROVAL_REQUIRED=false` in your environment
2. **Never** commit this configuration
3. Document the risk in your team's runbook

**Q: How do I add a new tool to an agent?**
A: Follow these steps:
1. Add the tool to `tools.py` in the read or write category
2. Register it in the orchestrator/agent
3. If it's a write tool, ensure it goes through the approval gate
4. Add tests for the tool
5. Document the tool in the module's README

**Q: Why no Kubernetes support?**
A: The current implementation uses serverless first (Lambda, Functions, Cloud Functions)
for simplicity and cost-effectiveness. Kubernetes is a valid extension and may be added
in the future. See [FUT-003](ENHANCEMENT-PLAN.md#task-43---hybrid-cloud-proof-of-concept) for
planned work.

## Security

**Q: Is the write boundary really unbreakable?**
A: No security control is absolute. The write boundary is enforced at the identity
platform level (IAM, Entra ID, GCP IAM), which is stronger than prompt-based or model-based
enforcement. However, see [THREAT-MODEL.md](THREAT-MODEL.md) for known limitations.

**Q: What if a model ignores its instructions and calls a write tool anyway?**
A: The orchestrator (not the model) controls tool access. Even if a model requests a
write action, the orchestrator checks the approval gate before executing. This is why
the separation of concerns matters.

## Troubleshooting

**Q: I get "ModuleNotFoundError" when running an example**
A: Install the example's dependencies:
```bash
pip install -r examples/<example-name>/requirements.txt
```

**Q: Terraform plan fails with "resource already exists"**
A: Run:

```bash
terraform import <resource_type>.<name> <resource_id>
```

Or destroy and recreate the resource.

**Q: Approval tokens keep expiring**
A: Tokens expire after 24 hours by default. To change this:

- AWS: Update `var.approval_token_ttl_seconds` in `modules/approval/variables.tf`
- Azure: Update `approval_token_ttl` in `modules/approval/main.tf`
- GCP: Update `approval_token_ttl` in `modules/approval/main.tf`

```

**Verify.**
```bash
test -f docs/FAQ.md && grep -c "^##" docs/FAQ.md  # Expect at least 3 sections
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

**Action.**

1. Create `tests/performance/` directory
2. Add `test_performance.py`:

   ```python
   import unittest
   import time
   import subprocess
   import statistics

   class TestPerformance(unittest.TestCase):
       def test_hermes_agent_latency(self):
           times = []
           for _ in range(10):
               start = time.time()
               subprocess.run(
                   ["python3", "examples/hermes-agent/agent.py", "--quiet", "test query"],
                   capture_output=True,
                   check=True
               )
               times.append(time.time() - start)

           avg = statistics.mean(times)
           p95 = sorted(times)[int(len(times) * 0.95)]

           print(f"Hermes Agent - Avg: {avg:.3f}s, P95: {p95:.3f}s")
           self.assertLess(avg, 5.0, "Hermes agent average latency too high")

       def test_graph_agent_latency(self):
           times = []
           for _ in range(10):
               start = time.time()
               subprocess.run(
                   ["python3", "examples/graph-agent/graph_agent.py", "test query"],
                   capture_output=True,
                   check=True
               )
               times.append(time.time() - start)

           avg = statistics.mean(times)
           print(f"Graph Agent - Avg: {avg:.3f}s")
           self.assertLess(avg, 10.0, "Graph agent average latency too high")
   ```

3. Add to `checks.yml`:

   ```yaml
   - name: Performance tests
     run: python3 -m unittest discover -s tests/performance -v
   ```

**Verify.**

```bash
python3 -m unittest tests.performance.test_performance -v
```

---

### Task 28 — Add runtime smoke tests to CI

**Goal.** Catch runtime issues that static checks miss.

**Action.**
Create `tests/smoke/` directory with:

- `test_example_smoke.py`:

  ```python
  import unittest
  import subprocess
  import sys

  class TestExampleSmoke(unittest.TestCase):
      EXAMPLES = [
          "hermes-agent",
          "starter-agent",
          "trace-eval",
          "graph-agent",
          "context-compaction",
          "checkpoint-agent",
      ]

      def test_example_runs(self):
          for example in self.EXAMPLES:
              with self.subTest(example=example):
                  result = subprocess.run(
                      [sys.executable, f"examples/{example}/agent.py", "--help"],
                      capture_output=True,
                      text=True
                  )
                  self.assertEqual(
                      result.returncode, 0,
                      f"{example} failed: {result.stderr}"
                  )
                  self.assertIn(
                      "usage" or "Agent" or example,
                      result.stdout + result.stderr,
                      f"{example} help output unexpected"
                  )
  ```

**Verify.**

```bash
python3 -m unittest tests.smoke.test_example_smoke -v
```

---

### Task 40 — Add evaluation as a service

**Goal.** Turn `trace-eval` into a reusable service for scoring agent traces.

**Action.**

1. Create `services/trace-eval-service/`:
   - `app.py`: FastAPI application exposing `/score` endpoint
   - `Dockerfile`: Container for the service
   - `requirements.txt`: Dependencies
   - `README.md`: Documentation

2. API design:

   ```python
   # services/trace-eval-service/app.py
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
test -f services/trace-eval-service/app.py
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
        "simple": {"name": "gpt-4o-mini", "max_tokens": 1000, "cost_per_token": 0.0000015},
        "complex": {"name": "gpt-4o", "max_tokens": 4000, "cost_per_token": 0.000005},
        "code": {"name": "claude-3-5-sonnet", "max_tokens": 4000, "cost_per_token": 0.000003},
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
grep -q "ModelRouter" examples/hermes-agent/hermes/router.py
```

---

### Task 42 — Add `memory-agent` example

**Goal.** Demonstrate long-term memory patterns for agents.

**Action.**
Create `examples/memory-agent/` with:

- Vector memory (FAISS)
- Graph memory (NetworkX)
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
python3 -c "from memory_agent.memory import VectorMemory, TimeDecayMemory; print('Import OK')"
```

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
```

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
```

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
```

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

---

## Links

- [README.md](../README.md) — Repository overview
- [REPO-AUDIT.md](REPO-AUDIT.md) — Previous audit and remediation (fully resolved)
- [HARDENING-PLAN.md](HARDENING-PLAN.md) — CI hardening tasks
- [CONCEPTS-PLAN.md](CONCEPTS-PLAN.md) — Conceptual additions
- [CONTRIBUTING.md](../CONTRIBUTING.md) — How to contribute
- [THREAT-MODEL.md](THREAT-MODEL.md) — Security threat model
