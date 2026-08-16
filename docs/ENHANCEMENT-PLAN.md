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

Update the status column as you go: `Not Started` → `In Progress` → `Done` → `Verified`.

---

## Priority Matrix

| Priority | Criteria | SLA |
|----------|----------|-----|
| High | Security hardening, critical gaps, blocks other work | 7 days |
| Medium | Functional improvements, new examples, docs | 30 days |
| Low | Nice-to-haves, refinements, future ideas | 90 days |

---

## Progress

| # | Task | Category | Priority | Status | Owner | Due Date |
|---|------|----------|----------|--------|-------|----------|
| 1 | Add `QUICKSTART.md` | Documentation | High | Not Started | | 2026-08-20 |
| 2 | Add pre-commit hooks | Repository | High | Not Started | | 2026-08-20 |
| 3 | Label `GOOD-FIRST-ISSUE` in GitHub | Community | High | Not Started | | 2026-08-20 |
| 4 | Document approval token TTL | Infrastructure | High | Not Started | | 2026-08-23 |
| 5 | Add secret scanning to CI | Security | High | Not Started | | 2026-08-23 |
| 6 | Add `terraform plan` to CI | CI/CD | High | Not Started | | 2026-08-23 |
| 7 | Add `MODULES.md` catalog | Documentation | High | Not Started | | 2026-08-23 |
| 8 | Add `checkpoint-agent` example | Examples | High | Not Started | | 2026-08-23 |
| 9 | Add `SECURITY.md` tests to CI | Security | High | Not Started | | 2026-08-30 |
| 10 | Document handler packaging divergence | Documentation | Medium | Not Started | | 2026-08-30 |
| 11 | Add SAST scanning to CI | Security | High | Not Started | | 2026-08-30 |
| 12 | Add issue templates | Community | High | Not Started | | 2026-08-23 |
| 13 | Document approval claim formats | Documentation | High | Not Started | | 2026-08-23 |
| 14 | Add `envs/staging` | Infrastructure | Medium | Not Started | | 2026-08-30 |
| 15 | Add Terraform policy-as-code (OPA) | Infrastructure | Medium | Not Started | | 2026-09-13 |
| 16 | Add `DECISION-LOGS/` with ADRs | Documentation | Medium | Not Started | | 2026-08-30 |
| 17 | Add cost monitoring module | Infrastructure | Medium | Not Started | | 2026-09-20 |
| 18 | Document secrets rotation | Infrastructure | Medium | Not Started | | 2026-09-06 |
| 19 | Add `HOW-TO-RECOVER.md` per cloud | Infrastructure | Medium | Not Started | | 2026-09-13 |
| 20 | Add `multi-agent-debate` example | Examples | Medium | Not Started | | 2026-09-06 |
| 21 | Add `tool-discovery` example | Examples | Medium | Not Started | | 2026-09-13 |
| 22 | Add `context-overflow` example | Examples | Medium | Not Started | | 2026-09-20 |
| 23 | Add `eval-red-teaming` example | Examples | Medium | Not Started | | 2026-09-27 |
| 24 | Update `graph-agent` for production | Examples | Medium | Not Started | | 2026-09-06 |
| 25 | Add `MIGRATION-GUIDE.md` | Documentation | Medium | Not Started | | 2026-09-13 |
| 26 | Add example dependency graph to CI | CI/CD | Medium | Not Started | | 2026-09-06 |
| 27 | Add performance tests to CI | CI/CD | Medium | Not Started | | 2026-09-20 |
| 28 | Add runtime smoke tests to CI | CI/CD | Medium | Not Started | | 2026-09-13 |
| 29 | Add `terraform plan` cost estimation | CI/CD | Medium | Not Started | | 2026-09-20 |
| 30 | Add approval gate fuzzing | Security | Medium | Not Started | | 2026-09-20 |
| 31 | Update `THREAT-MODEL.md` | Security | Medium | Not Started | | 2026-09-13 |
| 32 | Add `COMPLIANCE.md` | Documentation | Low | Not Started | | 2026-10-11 |
| 33 | Add discussion topics | Community | Low | Not Started | | 2026-10-04 |
| 34 | Add `ROADMAP.md` | Community | Low | Not Started | | 2026-09-13 |
| 35 | Add badges to README | Community | Low | Not Started | | 2026-10-11 |
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

Include prerequisites (Python 3.9+, Terraform 1.9.8+) and expected output.

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
        entry: bash -c 'cd infra && terraform validate -recursive -no-color'
        language: system
        pass_filenames: false
        files: ^infra/.*\.(tf|tfvars)$
      - id: python-compile
        name: python compile
        entry: python3 -m py_compile
        language: system
        files: \.py$
```

Add a `PRE-COMMIT.md` in `docs/` explaining how to install and use hooks.

**Verify.**
```bash
pre-commit run --all-files 2>&1 | grep -E "(Passed|Failed)" || echo "pre-commit not installed"
grep -q "pre-commit" CONTRIBUTING.md || echo "Add pre-commit setup to CONTRIBUTING.md"
```

---

### Task 3 — Label `GOOD-FIRST-ISSUE` in GitHub

**Goal.** Encourage community contributions by tagging beginner-friendly tasks.

**Action.**
1. Create a `GOOD-FIRST-ISSUE` label in the GitHub repository (color: `#70c87c`, green)
2. Label these tasks as `GOOD-FIRST-ISSUE`:
   - Add `MODULES.md` catalog (Task 7)
   - Add pre-commit hooks (Task 2)
   - Add `FAQ.md` (Task 39)
   - Convert Mermaid diagrams to code (Task 37)
3. Document the label in `CONTRIBUTING.md`

**Verify.**
```bash
# Check if label exists (requires GitHub CLI)
gh label list | grep -q "GOOD-FIRST-ISSUE" && echo "Label exists" || echo "Label missing"
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
Add a new job to `.github/workflows/checks.yml`:
```yaml
  secret-scan:
    name: Secret scanning
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.22'
      - name: Install gitleaks
        run: go install github.com/gitleaks/gitleaks/v8@latest
      - name: Scan for secrets
        run: gitleaks detect --source . --verbose
```

**Verify.**
```bash
# Test locally first
gitleaks detect --source . --dry-run
echo $?  # Expect 0 if clean
```

---

### Task 6 — Add `terraform plan` to CI

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
          terraform_version: 1.9.8
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
- Terraform version: [e.g., 1.9.8]
- Cloud: [AWS/Azure/GCP/None]

**Additional context**
Add any other context about the problem here.
```

2. **`feature_request.md`:**
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

3. **`security.md`:**
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

### Task 14 — Add `envs/staging`

**Goal.** Provide a canary deployment environment between dev and prod.

**Action.**
For each cloud tree (`terraform-aws`, `terraform-azure`, `terraform-gcp`):
1. Copy `envs/dev` to `envs/staging`
2. Update variable values to be production-like but with smaller scale:
   - AWS: Reduce Lambda memory to 512MB, Step Functions concurrency to 10
   - Azure: Reduce Function App memory to 512MB, Logic Apps concurrency to 10
   - GCP: Reduce Cloud Functions memory to 512MB, Workflows concurrency to 10
3. Add a `staging` entry to the CI matrix in `checks.yml`

**Verify.**
```bash
for cloud in aws azure gcp; do
  test -d infra/terraform-$cloud/envs/staging && echo "$cloud/staging: OK" || echo "$cloud/staging: MISSING"
done
grep -q "staging" .github/workflows/checks.yml && echo "CI updated" || echo "CI not updated"
```

---

### Task 18 — Document secrets rotation

**Goal.** Provide clear guidance for rotating sensitive credentials.

**Action.**
Create `docs/SECRETS-ROTATION.md` with sections for each cloud:

```markdown
# Secrets Rotation Guide

This document describes how to rotate all secrets used in the Agentic-AI-Systems deployments.

## General Principles

1. **Never commit secrets** to Git (enforced by `gitleaks` in CI)
2. **Use cloud secret managers** where possible (AWS Secrets Manager, Azure Key Vault, GCP Secret Manager)
3. **Rotate regularly** based on risk:
   - Model API keys: Every 90 days
   - Approval gate tokens: Every 24 hours (auto-rotated by default)
   - Database credentials: Every 180 days

## AWS

### Model API Keys (Bedrock)
1. Generate new key in AWS IAM: `aws iam create-access-key`
2. Update `modules/security/bedrock.tf`:
   ```hcl
   variable "bedrock_api_key" {
     default = "new-key-here"  # In production, use AWS Secrets Manager
   }
   ```
3. Redeploy: `terraform apply -target=module.security`

### Approval Gate DynamoDB Credentials
1. Rotate via AWS IAM: `aws iam create-access-key`
2. Update `modules/approval/dynamodb.tf`
3. Redeploy

## Azure

### Model API Keys (Azure OpenAI)
1. Generate new key in Azure Portal: Cognitive Services → Keys
2. Update `modules/model-integration/main.tf`
3. Redeploy

### Approval Gate Cosmos DB Credentials
1. Rotate via Azure Portal: Cosmos DB → Keys
2. Update `modules/approval/cosmos.tf`
3. Redeploy

## GCP

### Model API Keys (Vertex AI)
1. Generate new service account key: `gcloud iam service-accounts keys create`
2. Update `modules/security/vertex.tf`
3. Redeploy

### Approval Gate Firestore Credentials
1. Rotate via GCP IAM: IAM & Admin → Service Accounts
2. Update `modules/approval/firestore.tf`
3. Redeploy

## Automation

Use these scripts to automate rotation:

```bash
# AWS
./scripts/rotate-aws-secrets.sh

# Azure
./scripts/rotate-azure-secrets.sh

# GCP
./scripts/rotate-gcp-secrets.sh
```
```

**Verify.**
```bash
test -f docs/SECRETS-ROTATION.md && grep -c "AWS\|Azure\|GCP" docs/SECRETS-ROTATION.md
```

---

### Task 20 — Add `multi-agent-debate` example

**Goal.** Demonstrate multi-agent coordination patterns.

**Action.**
Create `examples/multi-agent-debate/` with:
- `README.md`: Explains the pattern (proposer, reviewer, approver agents)
- `agent.py`: Implements three agent types
- `requirements.txt`: Only stdlib (no external dependencies)
- `test_multi_agent.py`: Unit tests for the coordination logic

**Implementation:**
```python
# examples/multi-agent-debate/agent.py

class ProposerAgent:
    """Generates action proposals."""
    def propose(self, goal: str) -> dict:
        return {"action": "restart_service", "args": {"service": "billing"}, "rationale": "..."}

class ReviewerAgent:
    """Reviews proposals for safety and correctness."""
    def review(self, proposal: dict) -> bool:
        # Check if action is allowed
        return True

class ApproverAgent:
    """Approves or rejects based on reviewer feedback."""
    def approve(self, proposal: dict, review: bool) -> str:
        if review:
            return f"APPROVED: {proposal['action']}"
        return f"REJECTED: {proposal['action']}"
```

**Verify.**
```bash
python3 -m unittest discover -s examples/multi-agent-debate -v
test -f examples/multi-agent-debate/README.md
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
python3 examples/checkpoint-agent/agent.py "action1"
python3 -c "from checkpoint_agent.agent import CheckpointAgent; a = CheckpointAgent(); print(a.resume())"
test -f examples/checkpoint-agent/state.json
```

---

## Phase 3 — Documentation & Governance (Week 4-6: 2026-09-06 to 2026-09-20)

This phase focuses on **documentation completeness** and **governance improvements**.

### Task 15 — Add Terraform policy-as-code (OPA)

**Goal.** Enforce infrastructure policies programmatically.

**Action.**
1. Add `policies/` directory to each Terraform tree:
   ```
   infra/terraform-aws/policies/
   infra/terraform-azure/policies/
   infra/terraform-gcp/policies/
   ```

2. Add OPA policy files:
   - `no_write_without_approval.rego`:
     ```rego
     package terraform

     deny[msg] {
       input.resource.type == "aws_lambda_function"
       not has_approval_gate(input.resource)
       msg := sprintf("Lambda %s has no approval gate integration", [input.resource.name])
     }

     has_approval_gate(res) {
       res.iam_role.policy["Statement"][_].Effect == "Allow"
       res.iam_role.policy["Statement"][_].Action["aws:dynamodb:ConditionCheckItem"]
     }
     ```

   - `least_privilege.rego`:
     ```rego
     package terraform

     deny[msg] {
       input.resource.type == "aws_iam_role_policy"
       has_wildcard(input.resource.policy)
       msg := sprintf("IAM policy %s uses wildcard permissions", [input.resource.name])
     }

     has_wildcard(policy) {
       startswith(policy.Statement[_].Action[_], "*")
     }
     ```

3. Add `conftest` to CI:
   ```yaml
   - name: Run OPA policies
     run: conftest test infra/ --policy policies/
   ```

**Verify.**
```bash
conftest test infra/terraform-aws/ --policy infra/terraform-aws/policies/ 2>&1 | head -20
```

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

**Action.**
1. Create `scripts/dependency_graph.py`:
   ```python
   import pathlib
   import networkx as nx
   import json

   def build_dependency_graph():
       G = nx.DiGraph()
       for example_dir in pathlib.Path("examples").iterdir():
           if not example_dir.is_dir():
               continue
           requirements_file = example_dir / "requirements.txt"
           if requirements_file.exists():
               deps = [line.strip().split("==")[0].split(">=")[0].strip()
                       for line in requirements_file.read_text().splitlines()
                       if line.strip() and not line.startswith("#")]
               for dep in deps:
                   G.add_edge(str(example_dir.name), dep)
       return G

   if __name__ == "__main__":
       G = build_dependency_graph()
       print("Dependency graph:")
       for node in G.nodes():
           print(f"  {node}: {list(G.neighbors(node))}")

       # Check for cycles
       try:
           cycle = nx.find_cycle(G)
           print(f"ERROR: Circular dependency detected: {cycle}")
           exit(1)
       except nx.NetworkXNoCycle:
           print("No circular dependencies found")
   ```

2. Add to `checks.yml`:
   ```yaml
   - name: Check example dependencies
     run: python3 scripts/dependency_graph.py
   ```

**Verify.**
```bash
python3 scripts/dependency_graph.py
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
|------|--------|--------|
| 2026-08-16 | Initial enhancement plan created with 45 tasks across 8 categories | somesh-ghaturle |

---

## Links

- [README.md](../README.md) — Repository overview
- [REPO-AUDIT.md](REPO-AUDIT.md) — Previous audit and remediation (fully resolved)
- [HARDENING-PLAN.md](HARDENING-PLAN.md) — CI hardening tasks
- [CONCEPTS-PLAN.md](CONCEPTS-PLAN.md) — Conceptual additions
- [CONTRIBUTING.md](../CONTRIBUTING.md) — How to contribute
- [THREAT-MODEL.md](THREAT-MODEL.md) — Security threat model
