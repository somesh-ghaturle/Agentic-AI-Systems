# Hardening plan — 2026-08-14

A follow-on to [REPO-AUDIT.md](REPO-AUDIT.md). That audit read the repository against its own
claims and fixed what it found. This plan closes the gap that let those findings exist in the
first place: **the repository has no automated check that would have caught them.**

The audit's most serious finding — `rag-langchain` and `langchain-agent` importing a LangChain
v0.x API that no longer exists — was found by a human reading files. CI was green throughout.
It was green because five of the eight examples were verified by nothing: no test, no import
check, not even a syntax check. Pinned dependencies plus no update signal is how the pins got
stale, and nothing in the repository would have told anyone.

Every task here follows the workflow's existing constraint: **no cloud credentials, ever.** A
check that needs a subscription is a check that gets disabled the first time a secret expires.
Network access to PyPI is the one new dependency, and it is confined to a single job.

**Scope:** 1 workflow file, 1 new Dependabot config, 1 new lint config, 2 new documents.

**How to use this document.** Work top to bottom — the phases are ordered so the cheapest
checks land first and the slowest one is gated behind path filters. Every task carries the
exact change and the command that proves it worked. Tick the boxes as you go.

Every command runs from the **repository root** unless it says otherwise.

## Before you start

```bash
python3 --version        # 3.9+ for the examples; CI pins 3.12
terraform version        # phases 5 only
```

No task needs cloud credentials. Task 2 needs network access to resolve pins from PyPI.

---

## Progress

| # | Task | Phase | Severity | Status |
|---|---|---|---|---|
| 1 | Syntax-check every example | 1 | high | [x] |
| 2 | Install and import the five dependency-carrying examples | 1 | high | [x] |
| 3 | Assert e2e-agent still fails closed without its key | 1 | medium | [x] |
| 4 | Dependabot for pip, terraform, and github-actions | 2 | high | [x] |
| 5 | Relative-link check in CI | 3 | medium | [x] |
| 6 | Add SECURITY.md | 4 | medium | [ ] |
| 7 | Ruff config and lint job — parity with `terraform fmt` | 4 | low | [ ] |
| 8 | tflint and checkov over the three trees | 5 | low | [ ] |
| 9 | Reconcile the Terraform version pin | 5 | low | [ ] |
| 10 | Threat model for the write boundary | 6 | medium | [ ] |
| 11 | Single cloud-comparison page | 6 | low | [ ] |

Phases 1 and 2 are the agreed scope. Phases 3 onward are sequenced but not committed to.

---

## Phase 1 — Verify the examples (the gap that already bit)

Three of eight examples were covered by `tests/` when this plan was written (seven of eleven now): `starter-agent`, `hermes-agent`, and
`trace-eval`. The other five — `e2e-agent`, `langchain-agent`, `rag-faiss`, `rag-langchain`,
`ray-orchestrator` — are covered by nothing.

The two tasks below are deliberately separate jobs rather than one. Task 1 is free and runs on
every change; task 2 costs minutes and downloads `ray[default]` and `sentence-transformers`, so
it earns its own path filter. Collapsing them would mean either paying the slow cost for a typo
or losing the fast signal entirely.

### Task 1 — Syntax-check every example

**Severity: high.** Catches a broken example in about a second, with no dependencies at all.
This is strictly weaker than task 2 and does not replace it: `compileall` parses, it does not
import, so it cannot see a name that a library stopped exporting. It catches the other failure
mode — the example that was edited and never run.

Add to the `examples` job in [`.github/workflows/checks.yml`](../.github/workflows/checks.yml),
after the existing unittest step:

```yaml
      # Every example, not just the three with suites. compileall parses without importing,
      # so it needs none of their dependencies and finishes in about a second — which is what
      # makes it affordable on the unfiltered path alongside the suites above.
      #
      # What this catches is the example edited in place and never run again. What it cannot
      # catch is a dependency that stopped exporting a name, because parsing is not importing.
      # That is task 2's job, and it is a separate job because it is a thousand times slower.
      - name: All examples — syntax
        run: python3 -m compileall -q examples/
```

**Verify:**

```bash
python3 -m compileall -q examples/ && echo "all examples parse"
```

### Task 2 — Install and import the five dependency-carrying examples

**Severity: high.** This is the check that would have caught the LangChain breakage. Importing
`langchain_openai` against the pinned version is the only thing that proves the pin and the
code agree.

Three examples have empty `requirements.txt` files and are already covered by `tests/`, so the
matrix covers the five that carry dependencies.

Two details the matrix has to encode, both discovered by reading the files rather than assumed:

- **`e2e-agent/app.py` raises on import without `E2E_AGENT_API_KEY`.** That is deliberate —
  the audit removed a default `local-test-key` so the service fails closed. The import check
  must therefore export a throwaway key, and task 3 asserts the fail-closed path separately so
  this workaround cannot quietly become a regression.
- **Every other entry module is `__main__`-guarded**, so importing runs no work. Verified across
  all eight; `app.py` is the only exception, and it builds a FastAPI object rather than serving.

**Shipped as its own workflow, not as a job in `checks.yml`.** The first draft put it in
`checks.yml` behind an `if:` guard, which was wrong: that workflow already triggers only on
push and pull_request, so the guard was always true and gated nothing. Path filtering in
GitHub Actions is `on.paths`, which is per-workflow — a job that genuinely needs a different
trigger needs a different file. It lives in
[`.github/workflows/example-deps.yml`](../.github/workflows/example-deps.yml), firing only on
`examples/**` and `tests/**`.

```yaml
  imports:
    name: ${{ matrix.example }}
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        include:
          - example: e2e-agent
            modules: app
          - example: langchain-agent
            modules: agent
          - example: rag-faiss
            modules: build_index query
          - example: rag-langchain
            modules: build_index query_and_answer
          - example: ray-orchestrator
            modules: orchestrator
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: examples/${{ matrix.example }}/requirements.txt

      # The three examples with empty requirements files — hermes-agent, starter-agent,
      # trace-eval — are absent from this matrix on purpose: they are stdlib-only and the
      # `examples` job already runs their suites.
      - name: Install pinned dependencies
        run: pip install -q -r examples/${{ matrix.example }}/requirements.txt

      # The check that the audit needed and did not have. `rag-langchain` and
      # `langchain-agent` sat in this repository importing a LangChain v0.x API that the
      # pinned version had already deleted, and CI was green the whole time, because nothing
      # here had ever imported them. Parsing would not have caught it; only importing does.
      #
      # e2e-agent raises at import time when E2E_AGENT_API_KEY is unset — the fail-closed
      # behaviour the audit introduced by deleting a default key. Hence the throwaway value
      # here, and hence the separate assertion in the job below that the failure still happens
      # without it.
      - name: Import every entry module
        env:
          E2E_AGENT_API_KEY: ci-import-check
        working-directory: examples/${{ matrix.example }}
        run: |
          for m in ${{ matrix.modules }}; do
            echo "importing $m"
            python3 -c "import $m"
          done
```

**Verify** (one example, locally, in a throwaway venv):

```bash
python3 -m venv /tmp/dep-check
/tmp/dep-check/bin/pip install -q -r examples/langchain-agent/requirements.txt
(cd examples/langchain-agent && /tmp/dep-check/bin/python -c "import agent") && echo "imports clean"
```

### Task 3 — Assert e2e-agent still fails closed without its key

**Severity: medium.** Task 2 sets `E2E_AGENT_API_KEY` to make the import succeed. That is a
workaround for a security property, and a workaround for a security property should be pinned
down by a test, or the next person to see the env var will "simplify" it away.

Add to `tests/test_e2e_agent.py` (new file), following the stdlib-unittest convention every
other suite in this repository uses:

```python
"""Asserts e2e-agent refuses to start without an API key.

unittest rather than pytest: every other suite here is stdlib unittest and pytest is in no
requirements file. This suite is skipped unless the example's dependencies are installed,
so it is a no-op in the credential-free `examples` job and real in `example-deps`.
"""
```

The test imports `app` with the variable unset and asserts `RuntimeError`. Run it from the
`example-deps` job for `e2e-agent` only.

**Verify:**

```bash
/tmp/dep-check/bin/pip install -q -r examples/e2e-agent/requirements.txt
python3 -m unittest tests.test_e2e_agent -v
```

---

## Phase 2 — Keep the pins honest

### Task 4 — Dependabot for pip, terraform, and github-actions

**Severity: high.** Pinning every dependency is the right call and clearly deliberate — it is
what makes the examples reproducible. But pinned with no update signal is exactly how the
LangChain pins went stale, and phase 1 only tells you the pin is *broken*, not that it is *old*.
Dependabot closes the other half.

Three ecosystems, and the third is the one people forget: the workflow pins
`actions/checkout@v4`, `actions/setup-python@v5`, and `hashicorp/setup-terraform@v3`, which age
the same way.

Create [`.github/dependabot.yml`](../.github/dependabot.yml) with a `pip` entry per example
directory that has a non-empty `requirements.txt`, one `terraform` entry per tree, and one
`github-actions` entry. Group the updates so five examples do not open fifteen pull requests a
month.

**Verify:**

```bash
python3 -c "import yaml,sys; yaml.safe_load(open('.github/dependabot.yml')); print('valid')"
# then, after pushing: repository → Insights → Dependency graph → Dependabot
```

---

## Phase 3 — Documentation integrity

**Done 2026-08-15 as round-two Task 17 in [REPO-AUDIT.md](REPO-AUDIT.md),** which
supersedes this section: it carries the two false-positive findings (fenced code
blocks, `#fragment` suffixes) that this task was written without, and it also widened
the path filters so documentation changes trigger CI at all.

### Task 5 — Relative-link check in CI

**Severity: medium.** This repository is 67 markdown files and its primary output is prose. A
broken relative link is the one defect class that ships completely invisibly — it renders fine
until someone clicks. Both the audit and the README rewrite found broken links by hand.

Stdlib script over every `](path)` that is not `http` and not a bare anchor, asserting the
target exists. No new dependency, and it runs on markdown changes rather than the current
`infra`/`examples`/`tests` filter — which is why this task also has to widen the `on.paths`
list, since today a docs-only commit runs no CI at all.

**Two things a naive `grep` gets wrong, both established by writing one and reading its
output.** A one-liner reported 34 broken links across this repository and every one was a
false positive:

- **Fenced code blocks.** `REPO-AUDIT.md` and this document quote other files' markdown inside
  triple-backtick fences, including their relative links. Those resolve against the file being
  quoted, not the file quoting it. A checker must track fence state and skip what is inside.
  (Writing the fence marker literally in prose here would open a fence mid-paragraph and hide
  the rest of this list from the checker — which is the same bug, one level up.)
- **`#fragment` suffixes.** `ARCHITECTURE.md#6--what-terraform-builds` is a valid link to a
  file that exists; testing the whole string as a path fails. Split on `#` and test the left
  half. Whether the anchor itself resolves is a harder check and a separate task.

The real count, once both are handled, is zero. That is worth knowing before the job is
written: this task is about keeping it at zero, not about repairing a backlog.

**Verify** — a working implementation lives in the scratchpad used to produce this figure;
reimplement it in `tests/` or `.github/scripts/` when doing the task:

```bash
python3 .github/scripts/linkcheck.py .   # exits non-zero on the first broken link
```

---

## Phase 4 — Disclosure and language parity

### Task 6 — Add SECURITY.md

**Severity: medium.** A repository whose entire thesis is *a state-changing action cannot reach
production without a human approving that specific action* has no vulnerability disclosure path.
The gap is more conspicuous here than it would be in most repositories.

It should say what is in scope (the Terraform boundary modules, the two boundary examples), what
is explicitly out of scope (the minimal reference examples, which are teaching code and say so),
and how to report privately.

### Task 7 — Ruff config and lint job

**Severity: low.** The Terraform side gets `terraform fmt -check` in CI. The Python side has no
`pyproject.toml`, no ruff, no formatter, and no CI job. That asymmetry is visible to any reader
who opens both.

Minimal `pyproject.toml` with ruff configured for `py39` — the floor the examples claim — plus a
lint job. Expect a first run that fails on existing code; fix the findings in the same change
rather than lowering the rules to make it pass.

---

## Phase 5 — Terraform depth

### Task 8 — tflint and checkov

**Severity: low.** CI validates but never lints or policy-scans. Both tools run credential-free,
so they fit the existing constraint. Expect noise on first run; tune the ruleset rather than
disabling the job.

### Task 9 — Reconcile the Terraform CLI version pin

**This is the CLI, not the providers.** `.github/dependabot.yml` used to point here for the
provider-constraint decision; that was task 21 in [REPO-AUDIT.md](REPO-AUDIT.md), and it closed
on 2026-08-15 by pinning every provider to its major. Nothing below is affected by it.

**Severity: low.** CI pins 1.9.8. Local development is on 1.15.8. `fmt` agrees across that gap
and all seven roots validate on both, but the two are not guaranteed to stay agreed, and a
divergence found during a release is found at the worst time. Either raise the CI pin or state
the floor deliberately in the workflow comment.

---

## Phase 6 — Content

### Task 10 — Threat model for the write boundary

**Severity: medium.** Each tree's `ARCHITECTURE.md` section 2 explains *how* the boundary is
drawn, and is honest about Azure being genuinely thinner. What no document covers is the
adversary's view: what a compromised orchestrator reaches, what a prompt-injected model reaches,
what a leaked approval claim buys before it expires, and which of the three clouds survives each.

Most of this already exists as scattered justification across the three trees and the audit. One
document collecting it would be the thing that distinguishes this repository from every other
agentic-architecture repository, none of which have one.

### Task 11 — Single cloud-comparison page

**Severity: low.** The differences are documented per-tree, so a reader choosing between AWS and
GCP must read three `ARCHITECTURE.md` files and diff them mentally. The root README's table is a
service mapping, not a decision aid.

---

## Definition of done

Phases 1 and 2 only — the agreed scope.

```bash
# 1. Every example parses
python3 -m compileall -q examples/ && echo "parse OK"

# 2. Existing suites still pass
python3 -m unittest discover -s tests -v 2>&1 | tail -3

# 3. Workflow and Dependabot config are valid YAML
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/checks.yml')); \
            yaml.safe_load(open('.github/dependabot.yml')); print('yaml OK')"

# 4. No broken relative links introduced
grep -oE '\]\([^)#h][^)]*\)' README.md docs/HARDENING-PLAN.md | \
  sed 's/^[^:]*:](//;s/)$//' | sort -u

# 5. The Terraform side is untouched and still valid
terraform fmt -recursive -check infra/ && echo "fmt OK"
```
