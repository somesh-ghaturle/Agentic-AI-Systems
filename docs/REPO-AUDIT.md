# Repository audit and remediation plan — 2026-08-14

A full read of the repository against its own claims, and an end-to-end plan to close every
finding. Each item was reproduced or read directly from the file named; nothing here is
inferred from a summary.

The infrastructure is in good shape and the two newest examples are in good shape. Almost
everything that needs fixing sits in the older `examples/` folders, in documentation that
describes an earlier state of the repo, and in the gap between what CI checks and what the
repository now contains.

**Scope:** 312 tracked files, 67 markdown files, 3 Terraform trees, 8 examples, 234 tests.

**How to use this document.** Work top to bottom — the phases are ordered so that each one
is protected by the one before it. Every task carries the exact current text, the exact
replacement, and the command that proves it worked. Tick the boxes as you go.

Every command in this document runs from the **repository root** unless it says otherwise,
and every line number was read from the file named on 2026-08-14. If a line number no longer
matches, trust the quoted text over the number and search for it.

## Before you start

```bash
python3 --version        # 3.9+ for the examples; CI pins 3.12
terraform version        # CI pins 1.9.8 — needed for the Definition of done only
docker --version         # tasks 13 and 16 only
```

Tasks 2, 4, and 13 verify by importing `examples/e2e-agent/app.py`, which needs that
example's dependencies. Install them once into a throwaway virtualenv and use it for those
three tasks, or every verify step returns `ModuleNotFoundError: No module named 'fastapi'`
and tells you nothing about the fix:

```bash
python3 -m venv /tmp/e2e-venv
/tmp/e2e-venv/bin/pip install -q -r examples/e2e-agent/requirements.txt
# then substitute /tmp/e2e-venv/bin/python for python3 in those tasks' verify blocks
```

No task needs cloud credentials. Task 11 needs network access to resolve pins; task 13's
second verify line needs a working Docker daemon.

---

## Progress

| # | Task | Phase | Severity | Status |
|---|---|---|---|---|
| 1 | Add a LICENSE | 1 | high | [x] |
| 2 | Fix e2e-agent's artifact paths | 2 | high | [x] |
| 3 | Ignore audit logs and provenance | 2 | high | [x] |
| 4 | Modernise timestamps in e2e-agent | 2 | low | [x] |
| 5 | Run example tests in CI | 3 | medium | [x] |
| 6 | Convert `tests/test_agent.py` to unittest | 3 | medium | [x] |
| 7 | Rewrite the root README's CI section | 4 | medium | [x] |
| 8 | Point architecture docs at all three trees | 4 | medium | [x] |
| 9 | Add the two newest examples to the architecture doc | 4 | medium | [x] |
| 10 | Add the missing example link and group the list by depth | 4 | medium | [x] |
| 11 | Repair the two LangChain examples | 5 | high | [x] |
| 12 | Pin example dependencies | 5 | medium | [x] |
| 13 | Close e2e-agent's three security gaps | 6 | medium | [x] |
| 14 | Note where model configuration lives on AWS | 6 | low | [x] |
| 15 | Convert `e2e-agent/architecture.mmd` | 6 | low | [x] |
| 16 | Drop the obsolete Compose `version` key | 6 | low | [x] |

---

## Phase 1 — Legal (do this first)

Everything else in the repository is unusable by an organisation until this lands, which is
why a one-file task outranks four correctness bugs.

### Task 1 — Add a LICENSE

**Finding.** There is no `LICENSE` at the root. [CONTRIBUTING.md](../CONTRIBUTING.md)
invites forks and pull requests, and the README describes the repository as something
practitioners should clone and take templates from. Without a license, default copyright
applies and none of that is something a company can legally do.

**Fix.**

**Step 1 — choose Apache-2.0.** It is the convention for infrastructure reference material
that organisations are expected to copy, because of its explicit patent grant. MIT is
defensible if simplicity matters more, but the Terraform trees are the kind of artifact
corporate legal review is happiest to see under Apache-2.0.

**Step 2 — write the canonical text** to `LICENSE`, verbatim from
<https://www.apache.org/licenses/LICENSE-2.0.txt>. Do not retype or paraphrase it; an
altered license text is worse than none.

**Step 3 — fill the copyright line** at the end of the appendix with the year and owner.

**Step 4 — add a `## License` section** to the root README:

```markdown
## License

Apache License 2.0 — see [LICENSE](LICENSE). The Terraform trees and examples are intended
to be copied into your own repositories and adapted.
```

**Verify.**

```bash
test -f LICENSE && head -2 LICENSE && grep -c "License" README.md
```

---

## Phase 2 — Data correctness in e2e-agent

Two bugs that affect anyone who runs the example, plus one deprecation while the file is
open.

### Task 2 — Fix e2e-agent's artifact paths

**Finding.** [`app.py:35-37`](../examples/e2e-agent/app.py) hardcodes paths relative to the
repository root:

```python
AUDIT_LOG = "examples/e2e-agent/audit.log"
PROV_DIR = "examples/e2e-agent/provenance"
os.makedirs(PROV_DIR, exist_ok=True)
```

The example's own README tells you to `cd examples/e2e-agent` before starting the server.
Reproduced from that working directory:

```text
./examples
./examples/e2e-agent
./examples/e2e-agent/provenance
```

The demo creates `examples/e2e-agent/examples/e2e-agent/provenance/` and writes the audit
log two levels below where every instruction says to look. The container hits the same bug
by another route: the Dockerfile sets `WORKDIR /app` and copies the example flat, so the
paths resolve under `/app/examples/e2e-agent/`.

Nothing crashes, which is what makes it worth fixing — the example appears to work while
the governance artifacts it exists to demonstrate land where nobody looks.

**Fix.** Anchor to `__file__`, the way [`rag-faiss/build_index.py`](../examples/rag-faiss/build_index.py)
already anchors its index, and allow an environment override so a container can point them
at a mounted volume.

Add to the imports:

```python
from pathlib import Path
```

Replace lines 35-37:

```python
AUDIT_LOG = "examples/e2e-agent/audit.log"
PROV_DIR = "examples/e2e-agent/provenance"
os.makedirs(PROV_DIR, exist_ok=True)
```

with:

```python
# Anchored to this file, not to the working directory. The README says to `cd` here before
# starting the server, and a repo-root-relative path under that instruction silently builds
# examples/e2e-agent/examples/e2e-agent/ and writes the audit trail into it. Nothing fails;
# the artifacts just stop being where every instruction says they are.
HERE = Path(__file__).resolve().parent
AUDIT_LOG = Path(os.environ.get("E2E_AGENT_AUDIT_LOG", HERE / "audit.log"))
PROV_DIR = Path(os.environ.get("E2E_AGENT_PROV_DIR", HERE / "provenance"))
PROV_DIR.mkdir(parents=True, exist_ok=True)
```

Then update the one path join at line 66:

```python
    path = os.path.join(PROV_DIR, f"{trace_id}.json")
```

to:

```python
    path = PROV_DIR / f"{trace_id}.json"
```

`open(AUDIT_LOG, "a")` at line 61 needs no change — it already accepts a `Path`.

**Verify.** From two different working directories, confirm the artifacts land next to the
source file both times:

```bash
cd examples/e2e-agent && python3 -c "import app" && ls -d provenance && cd ../..
python3 -c "import sys; sys.path.insert(0,'examples/e2e-agent'); import app" \
  && ls -d examples/e2e-agent/provenance
test ! -d examples/e2e-agent/examples && echo "no nested path created"
```

### Task 3 — Ignore audit logs and provenance

**Finding.** `git check-ignore` reports neither `examples/e2e-agent/audit.log` nor
`examples/e2e-agent/provenance/*.json` as ignored. Both contain full request and response
payloads by design — [`app.py:90`](../examples/e2e-agent/app.py) builds
`{"prompt": prompt, "response": out, "user_id": req.user_id}` and hands it to `audit_entry`
([`app.py:55-62`](../examples/e2e-agent/app.py)), which appends it to the log.

Running the example leaves prompt content in the working tree, ready to be staged by the
next `git add .`.

**Fix.** Append to [`.gitignore`](../.gitignore), under the build-artifacts section:

```gitignore
# ---------------------------------------------------------------------------
# Example run artifacts
# ---------------------------------------------------------------------------

# e2e-agent writes the full prompt, response, and user id into every audit entry and one
# provenance file per request. Both are produced by running the demo, and both are exactly
# the kind of content that should never reach a commit. The Terraform patterns above guard
# against a 580 MB push; these guard against a smaller and more embarrassing one.
examples/e2e-agent/audit.log
examples/e2e-agent/provenance/

# rag-* build a local index on first run.
examples/rag-faiss/index.faiss
examples/rag-langchain/index.faiss
```

**Verify.**

```bash
git check-ignore -v examples/e2e-agent/audit.log examples/e2e-agent/provenance/x.json
git status --short   # must stay clean after running the example
```

### Task 4 — Modernise timestamps in e2e-agent

**Finding.** [`app.py:58` and `app.py:96`](../examples/e2e-agent/app.py) call
`datetime.utcnow()`, deprecated since Python 3.12. The Dockerfile pins `python:3.11-slim`
so it is silent today and will start warning the moment the base image moves.

**Fix.** Change the import:

```python
from datetime import datetime
```

to:

```python
from datetime import datetime, timezone
```

Add a helper next to the other module-level functions:

```python
def _timestamp() -> str:
    """Timezone-aware UTC, rendered with a Z suffix.

    `utcnow()` returns a naive datetime that merely happens to hold UTC — appending "Z" to
    it is an assertion the object cannot back. This produces the identical string from a
    value that actually carries its offset.
    """
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
```

Then replace both occurrences of:

```python
        "timestamp": datetime.utcnow().isoformat() + "Z",
```

with:

```python
        "timestamp": _timestamp(),
```

**Verify.**

```bash
# Match the call, not the word: the docstring above deliberately names `utcnow()` to explain
# why it went, so a bare grep for "utcnow" returns 1 and always will.
grep -c "datetime\.utcnow" examples/e2e-agent/app.py   # expect 0
python3 -W error::DeprecationWarning -c \
  "import sys; sys.path.insert(0,'examples/e2e-agent'); import app; print(app._timestamp())"
```

---

## Phase 3 — CI coverage

Until this lands, every fix in phases 4 to 6 is unprotected.

### Task 5 — Run example tests in CI

**Finding.** `terraform.yml:15-24` — since renamed by this task to
[`checks.yml`](../.github/workflows/checks.yml) — triggered only on:

```yaml
paths:
  - "infra/**"
  - ".github/workflows/terraform.yml"
```

The repository has 66 tests under `tests/` covering `examples/hermes-agent` and
`examples/trace-eval`, and none run on any push or pull request. Break the Hermes write
boundary and it merges green.

There is a real tension worth naming rather than papering over: the workflow was
deliberately consolidated to one file, and it is named `terraform`. Widening its paths makes
the name wrong.

**Fix — recommended (Option A): rename and widen.** Keeps the one-workflow decision.

**Step 1 — rename the file.**

```bash
git mv .github/workflows/terraform.yml .github/workflows/checks.yml
```

**Step 2 — change the workflow name and paths:**

```yaml
name: checks

on:
  push:
    branches: [main]
    paths:
      - "infra/**"
      - "examples/**"
      - "tests/**"
      - ".github/workflows/checks.yml"
  pull_request:
    paths:
      - "infra/**"
      - "examples/**"
      - "tests/**"
      - ".github/workflows/checks.yml"
```

**Step 3 — add a job after `write-boundary`:**

```yaml
  examples:
    name: examples
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      # Both example suites, one runner, no dependencies — the same reasoning as the
      # write-boundary job above. hermes-agent asserts that a write cannot happen by the
      # router's path; trace-eval asserts that its own checks still catch a run that
      # bypasses it. Neither needs a model, a network, or a cloud account, which is what
      # makes them safe to gate merges on.
      - name: Example suites — hermes-agent and trace-eval
        run: python3 -m unittest discover -s tests -v
```

**Step 4 — update branch protection.** Renaming the file renames the checks. If `main`
requires status checks named `terraform / fmt` and so on, those become `checks / fmt` and
the old names will sit permanently pending. Update the rule in the same change, or the first
PR after this lands cannot merge.

**Fix — Option B: second workflow.** If branch protection is awkward to change, leave
`terraform.yml` untouched and add `.github/workflows/examples.yml` with the job above and
`paths: ["examples/**", "tests/**", ".github/workflows/examples.yml"]`. Costs a second file;
keeps every existing check name.

**Verify.**

```bash
python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/checks.yml')); print('yaml ok')"
python3 -m unittest discover -s tests -v   # what the job runs
```

### Task 6 — Convert `tests/test_agent.py` to unittest

**Finding.** The file uses bare `def test_*` functions with plain `assert`, which is pytest
style. `unittest` does not collect them:

```console
$ python3 -m unittest discover -s tests -p "test_agent.py"
Ran 0 tests in 0.000s
NO TESTS RAN
```

pytest appears in no `requirements.txt` in the repository and no CI job installs it. These
two tests have never run — not locally, not in CI — and they are the only coverage
`examples/starter-agent` has. Task 5 will not pick them up either, because
`unittest discover` skips them silently rather than failing.

The file also builds a repo-root-relative path, so it only works from one directory — the
same class of bug as Task 2.

**Fix.** Replace the whole of [`tests/test_agent.py`](../tests/test_starter_agent.py) with:  <!-- renamed to test_starter_agent.py on 2026-08-15; see round-two Task 18 -->

```python
"""Smoke tests for the starter agent.

unittest rather than pytest: every other suite in this repository — both example suites and
all six under infra/ — is stdlib unittest, and pytest is in no requirements file here. As
bare pytest-style functions these tests were collected by nothing and had never run.

    python3 -m unittest tests.test_agent -v
"""

import pathlib
import subprocess
import sys
import unittest

AGENT = (
    pathlib.Path(__file__).resolve().parent.parent
    / "examples"
    / "starter-agent"
    / "agent.py"
)


def run_agent(args):
    """Run the agent as a subprocess, the way a user would.

    The path is derived from this file rather than the working directory, so the suite
    passes from anywhere instead of only from the repository root.
    """
    result = subprocess.run(
        [sys.executable, str(AGENT)] + args, capture_output=True, text=True
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


class TestStarterAgent(unittest.TestCase):
    def test_agent_echoes_an_unmatched_prompt(self):
        code, out, err = run_agent(["hello"])
        self.assertEqual(code, 0, err)
        self.assertIn("Agent received", out)

    def test_agent_selects_the_search_action(self):
        code, out, err = run_agent(["please", "search", "for", "X"])
        self.assertEqual(code, 0, err)
        self.assertIn("Action: search", out)


if __name__ == "__main__":
    unittest.main()
```

**Verify.** The count must go from 66 to 68, and must hold from a different directory:

```bash
python3 -m unittest discover -s tests            # expect: Ran 68 tests ... OK

# From elsewhere. Both paths are the tests directory: `tests/` has no __init__.py, so it is
# not importable as a package, and passing the repository root as -t fails with
# "Start directory is not importable" before a single test runs.
repo="$PWD"
(cd /tmp && python3 -m unittest discover -s "$repo/tests" -t "$repo/tests")
```

---

## Phase 4 — Stale documentation

Cheap, and it is what a new reader encounters first.

### Task 7 — Rewrite the root README's CI section

**Finding.** [`README.md:122`](../README.md) claims write-boundary tests exist "for Azure
and GCP", and line 124 says "AWS needs no equivalent, because there the same mistake is a
plan-time error rather than a quiet one."

Both are false. `infra/terraform-aws/tests/` holds 11 tests and the workflow runs them at
`terraform.yml:108-109`, now [`checks.yml`](../.github/workflows/checks.yml).
The suite's own header
explains why the original reasoning was incomplete: the
resource-policy half is a plan-time error, the identity-policy half is not, and widening
`var.tool_function_arns` passes `terraform validate` in silence.

The section also lists three of the five jobs that exist.

**Fix.** Replace the whole `## CI` section with:

```markdown
## CI

[`.github/workflows/checks.yml`](.github/workflows/checks.yml) runs on any change under
`infra/`, `examples/`, or `tests/`:

- `terraform fmt -check` across all three trees
- `terraform validate` on each of the seven environment roots, as a matrix so one broken root does not hide the others
- Write-boundary tests for all three trees — stdlib `unittest` reading `.tf` files as text
- Handler logic tests for all three trees
- Deployment package builds for all three trees
- Both example suites — `hermes-agent` and `trace-eval`

Everything runs without cloud credentials, which is deliberate: a check that needs a
subscription is a check that gets disabled the first time a secret expires.

The write-boundary tests exist because `terraform validate` accepts every mistake they
catch — in each case the wrong value is a valid value in a valid attribute. AWS was
originally excluded on the grounds that its boundary is a Lambda resource policy, so getting
it wrong fails at plan time. That turned out to be true of the resource policy and only of
it: for a caller in the same account Lambda grants invocation if the *identity* policy
allows it **or** the resource policy does, and the orchestrator's identity policy is built
from a list nothing checked. Widening that list to every tool is a one-word edit that plans,
validates, and applies cleanly. The AWS suite guards that half.
```

If you took Option B in Task 5, keep the `terraform.yml` link and add a second sentence for
the examples workflow.

**Verify.**

```bash
grep -n "AWS needs no equivalent" README.md   # expect no match
grep -n "checks.yml" README.md
```

### Task 8 — Point architecture docs at all three trees

**Finding.** [`docs/agentic-system-architecture/README.md:29`](agentic-system-architecture/README.md)
has one infra row:

```markdown
| [infra/terraform-aws/](../../infra/terraform-aws/README.md) | This architecture as Terraform on AWS — one module per building block |
```

The Azure and GCP trees are complete, validate, and carry their own `ARCHITECTURE.md`. A
reader arriving through the architecture doc — the intended path — never learns they exist.

**Fix.** Replace that row with:

```markdown
| [infra/](../../infra/) | This architecture as Terraform on three clouds — [AWS](../../infra/terraform-aws/README.md), [Azure](../../infra/terraform-azure/README.md), [GCP](../../infra/terraform-gcp/README.md), each with its own `ARCHITECTURE.md` drawn in that cloud's terms |
```

One row rather than three: the trees are at parity in structure, and the comparison between
them belongs in one place — the root README already carries that table.

**Verify.**

```bash
grep -n "infra/" docs/agentic-system-architecture/README.md | head -3
```

### Task 9 — Add the two newest examples to the architecture doc

**Finding.** Lines 80-86 of the same file list `starter-agent`, `rag-faiss`,
`rag-langchain`, `ray-orchestrator`, and `e2e-agent`, omitting `hermes-agent` and
`trace-eval` — the two examples that most directly implement what the document describes:
the tool read/write split, approval gates, and the trace-level evaluation feedback edge the
same README calls essential.

**Fix.** Replace that paragraph with:

```markdown
**Want to see the patterns in code:** the [examples/](../../examples/) directory has
runnable implementations. Two implement the building blocks directly —
[hermes-agent](../../examples/hermes-agent/README.md) is the tool read/write split and the
approval gate in application code, and [trace-eval](../../examples/trace-eval/README.md) is
the evaluation feedback edge above, scoring the path a run took rather than only the answer
it gave. Both are standard library only. Alongside them are smaller references:
[starter-agent](../../examples/starter-agent/README.md),
[rag-faiss](../../examples/rag-faiss/README.md),
[rag-langchain](../../examples/rag-langchain/README.md),
[ray-orchestrator](../../examples/ray-orchestrator/README.md), and
[e2e-agent](../../examples/e2e-agent/README.md) with its architecture diagram, model card,
datasheet, and SLA.
```

**Note the drift risk.** Examples are now enumerated in three places — the root README, this
document, and the folder. Two of the three will go stale again. Worth considering a single
`examples/README.md` index that the other two link to instead of listing.

**Verify.**

```bash
grep -c "hermes-agent\|trace-eval" docs/agentic-system-architecture/README.md
```

### Task 10 — Add the missing example link and group the list by depth

**Finding.** Two separate problems in the same place.

*One example is missing outright.* The README links seven of the eight — `rag-langchain`
appears nowhere in it:

```bash
$ for e in starter-agent rag-faiss rag-langchain langchain-agent ray-orchestrator \
           e2e-agent hermes-agent trace-eval; do
    printf "%-18s %s\n" "$e" "$(grep -c "examples/$e/" README.md)"
  done
rag-langchain      0        # every other example: 1
```

*And the seven that are listed are split by the wrong axis.* `starter-agent` sits in the
checklists block at line 100, between the privacy checklist and CONTRIBUTING; the other six
sit under "More runnable templates (examples):" at lines 104-110. Nothing in either block
distinguishes depth, and the examples are nowhere near uniform in it:

| Example | Python lines |
|---|---|
| `starter-agent` | 24 |
| `ray-orchestrator` | 28 |
| `langchain-agent` | 53 |
| `rag-faiss` | 65 |
| `rag-langchain` | 88 |
| `e2e-agent` | 109 |
| `trace-eval` | 1,044 |
| `hermes-agent` | 1,068 |

The first six are scripts; the last two are worked examples with tests, mutation-tested
checks, and architecture documents. A visitor clicking the first link lands on a 24-line
keyword `if` chain.

This is not an argument for padding the small ones — it is an argument that the list should
say which is which.

**Fix.** Replace both list blocks in the root README with the three below. This also adds
the missing `rag-langchain` link and moves `starter-agent` out of the checklists block:

```markdown
**Worked examples** — tests, architecture notes, and no dependencies:

- [hermes-agent](examples/hermes-agent/README.md) — routing and the write boundary in application code
- [trace-eval](examples/trace-eval/README.md) — trace-level evaluation, scoring the path rather than the answer

**Applied example** — tracing, audit, provenance, and governance docs over HTTP:

- [e2e-agent](examples/e2e-agent/README.md)

**Minimal references** — short scripts showing one idea each:

- [starter-agent](examples/starter-agent/README.md) — the smallest possible agent loop
- [rag-faiss](examples/rag-faiss/README.md) — build and query a local vector index
- [rag-langchain](examples/rag-langchain/README.md) — the same, through LangChain
- [langchain-agent](examples/langchain-agent/README.md) — a minimal LangChain agent
- [ray-orchestrator](examples/ray-orchestrator/README.md) — parallel task execution with Ray
```

Delete line 100 — the `Starter agent example:` bullet — from the
checklists block — it is now covered under "Minimal references". Leave the other five lines
in that block (the audit, the three checklists, and CONTRIBUTING) where they are; they are
not examples and do not belong in this list.

**Verify.** All eight examples linked exactly once, and `starter-agent` no longer sitting
among the checklists:

```bash
for e in starter-agent rag-faiss rag-langchain langchain-agent ray-orchestrator \
         e2e-agent hermes-agent trace-eval; do
  printf "%-18s %s\n" "$e" "$(grep -c "examples/$e/" README.md)"
done   # expect 1 on every row, including rag-langchain
grep -n "Starter agent example" README.md   # expect no match
```

---

## Phase 5 — Dependencies

The largest piece of work, and the two halves are the same problem.

### Task 11 — Repair the two LangChain examples

**Finding.** [`langchain-agent/agent.py:18-19`](../examples/langchain-agent/agent.py) and
[`rag-langchain/query_and_answer.py:31-32`](../examples/rag-langchain/query_and_answer.py)
both do:

```python
from langchain import LLMChain, PromptTemplate
from langchain.llms import OpenAI
```

These target the pre-0.2 top-level API. Both `requirements.txt` files ask for
`langchain>=0.0.300`, which resolves to **1.3.15** — `LLMChain` and `PromptTemplate` are no
longer exported from the package root, and `langchain.llms` moved to `langchain_community`
long before that. `openai>=0.27.0` has the same shape of problem: it resolves to **3.0.0**,
two rewrites past the API this code was written against.

Checked on 2026-08-14 with `pip index versions`. Installing `langchain-core` and
`langchain-openai` does not pull the old top-level `langchain` distribution at all, so the
original import is now a bare `ModuleNotFoundError: No module named 'langchain'`.

The second half is worse. Both call sites wrap the import in `except Exception` and return:

> "LangChain or OpenAI not installed — install requirements to run with real LLM."

A user who followed the README and installed the requirements is told the requirements are
not installed. The diagnosis is wrong, so the obvious next step cannot help, and the real
cause stays invisible.

**Fix.** Move to the current composition API and let the error speak.

Replace the body of `run_with_langchain` in `examples/langchain-agent/agent.py`:

```python
def run_with_langchain(prompt: str) -> str:
    # ImportError only. A bare `except Exception` here reported "not installed" for every
    # failure including a version mismatch, which sent people to reinstall a package that
    # was already present and correct.
    try:
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import ChatOpenAI
    except ImportError as error:
        return (
            f"LangChain is not installed or is a version this example does not target: "
            f"{error}. Install the pinned requirements.txt."
        )

    if not os.environ.get("OPENAI_API_KEY"):
        return "OPENAI_API_KEY not set — set it to use the OpenAI model."

    template = ChatPromptTemplate.from_messages(
        [("system", PROMPT), ("human", "{input}")]
    )
    # LCEL: the pipe replaces LLMChain, which is deprecated in the 0.3 line.
    chain = template | ChatOpenAI(temperature=0.2) | StrOutputParser()
    return chain.invoke({"input": prompt}).strip()
```

Apply the same three changes to `rag-langchain/query_and_answer.py` — the imports, the
`except ImportError`, and the LCEL pipe.

Then replace both `requirements.txt` files. The package split matters: `langchain_openai`
lives in its own distribution now.

```text
langchain-core==<pin>
langchain-openai==<pin>
```

**Do not guess the pins.** Resolve them once and record what you got:

```bash
python3 -m venv /tmp/lcvenv && /tmp/lcvenv/bin/pip install langchain-core langchain-openai
/tmp/lcvenv/bin/pip freeze | grep -E "^(langchain|openai|tiktoken)"
```

Paste those exact `==` lines into both files.

**Verify.** The fallback path must produce an honest message, and the real path must run:

```bash
python3 examples/langchain-agent/agent.py "hello"          # no key set: says so
OPENAI_API_KEY=... python3 examples/langchain-agent/agent.py "hello"
```

If you would rather not carry a LangChain dependency at all, the alternative is to call the
provider SDK directly and delete `langchain-agent`. The repository already demonstrates
agent structure without a framework twice over, so the example's remaining value is showing
the framework specifically — which is only worth having if it works.

### Task 12 — Pin example dependencies

**Finding.** [CONTRIBUTING.md](../CONTRIBUTING.md) says "Prefer reproducible examples and
pinned dependencies." Across all 21 `requirements.txt` files there is not one `==`.
Everything is `>=` or bare — `fastapi`, `uvicorn[standard]`, `faiss-cpu`, and `numpy` carry
no constraint at all. Task 11 is what that produces in practice: an unbounded range that
quietly crossed a breaking change.

**Fix.** For each of the five examples that have dependencies — `hermes-agent`,
`starter-agent`, and `trace-eval` have none — resolve and pin:

```bash
for ex in e2e-agent langchain-agent rag-faiss rag-langchain ray-orchestrator; do
  python3 -m venv "/tmp/pin-$ex"
  "/tmp/pin-$ex/bin/pip" install -q -r "examples/$ex/requirements.txt"
  "/tmp/pin-$ex/bin/pip" freeze > "/tmp/pin-$ex.txt"
  echo "=== $ex ==="; cat "/tmp/pin-$ex.txt"
done
```

Then write the *direct* dependencies back with `==` at the versions that resolved. Pin the
direct ones rather than pasting the whole freeze: a full transitive freeze is reproducible
but becomes unreadable and unmaintainable in an example whose job is to be read.

Keep the header comment style `hermes-agent` and `trace-eval` already use, so the reason is
on the page:

```text
# Pinned rather than floored. This example previously carried `langchain>=0.0.300`, which
# resolved to a line where its own imports no longer exist — see docs/REPO-AUDIT.md task 11.
```

**`infra/**/requirements.txt` is a separate judgement.** Those 13 files carry cloud SDK
floors, and floors are more defensible there because the handlers are deployed rather than
demonstrated, and because the SDKs hold a stronger compatibility line than the LLM framework
ecosystem does. Decide explicitly and write the decision into
[`infra/terraform-aws/README.md`](../infra/terraform-aws/README.md) rather than leaving it
as an unstated default.

**Verify.**

```bash
# Expect exactly three: hermes-agent, starter-agent, trace-eval — the ones with no
# dependencies to pin. Any other file listed here still carries a floor or a bare name.
grep -L "==" examples/*/requirements.txt
```

---

## Phase 6 — Consistency and polish

### Task 13 — Close e2e-agent's three security gaps

**Finding.** The example is titled "Secure, Observable, Auditable". The observability and
audit halves are earned; the security half overclaims.

1. [`app.py:32`](../examples/e2e-agent/app.py) — `API_KEY = os.environ.get("E2E_AGENT_API_KEY", "local-test-key")`.
   Deployed without the variable set, the service authenticates against a constant
   published in this repository. The README discloses it as a demo choice; failing closed
   costs one line.
2. [`app.py:75`](../examples/e2e-agent/app.py) — `if key != API_KEY` is a non-constant-time
   comparison. Low practical risk, and this is the one example explicitly about doing
   security properly.
3. The Dockerfile has no `USER`, so the container runs as root.

**Fix.** Add `import hmac` to the imports, then replace line 32:

```python
API_KEY = os.environ.get("E2E_AGENT_API_KEY", "local-test-key")
```

with:

```python
# Fails closed. A default here means that anyone who deploys this without reading the README
# is authenticating against a constant published in a public repository — and it is exactly
# the demo convenience that gets copied into something real.
API_KEY = os.environ.get("E2E_AGENT_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "E2E_AGENT_API_KEY must be set. For a local demo: export E2E_AGENT_API_KEY=local-test-key"
    )
```

Replace the check at line 75:

```python
    if key != API_KEY:
```

with:

```python
    # Constant-time: `!=` on a secret returns as soon as it finds a differing byte, which
    # leaks the length of the matching prefix to anyone who can time the response.
    if not hmac.compare_digest(key or "", API_KEY):
```

And in the Dockerfile, before `CMD`:

```dockerfile
# Non-root. The app writes its audit log and provenance files into its own directory, so
# the working tree has to be owned by the user that runs it.
RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
USER appuser
```

Update the example's README so the SLA and governance sections describe the new fail-closed
behaviour rather than the old default.

**Verify.**

```bash
(unset E2E_AGENT_API_KEY; python3 -c "import sys; sys.path.insert(0,'examples/e2e-agent'); import app") \
  2>&1 | grep -q RuntimeError && echo "fails closed"
docker build -t e2e-check examples/e2e-agent && docker run --rm e2e-check id
```

### Task 14 — Note where model configuration lives on AWS

**Finding.** Module inventories differ across the trees:

| Tree | Modules |
|---|---|
| AWS | approval, archive, knowledge, observability, orchestration, security, state, tools (8) |
| Azure | + entra-audit, identity, model-integration, networking (12) |
| GCP | + identity, model-integration (10) |

AWS has no `model-integration` module — Bedrock configuration lives in `modules/security/` —
and no `identity` module, with IAM roles declared inside each module that needs one. Those
are placement decisions rather than missing capability, and the root README is careful to
say the trees are at parity "in structure, not in implementation".

But `docs/agentic-system-architecture/README.md:29` describes the AWS tree as "one module
per building block", and model routing is one of the six building blocks. For AWS it is not
its own module. Task 8 removes that phrase; this task records where the thing actually is.

**Fix.** Add to [`infra/terraform-aws/README.md`](../infra/terraform-aws/README.md), near
the module list:

```markdown
**Where the model layer lives.** AWS has no `model-integration/` module, unlike the Azure
and GCP trees. Bedrock model access and the guardrail are declared in `modules/security/`,
because on AWS the model layer *is* an access-control surface: there is no account resource
to create, only an IAM policy naming the model ARNs and a `aws_bedrock_guardrail` attached
to them. Azure and GCP both need a first-class account or endpoint resource, so both earn a
module. Identity is distributed the same way — each module declares the roles it needs
rather than a central `identity/` module owning them.
```

**Verify.**

```bash
grep -n "model-integration" infra/terraform-aws/README.md
```

### Task 15 — Convert `e2e-agent/architecture.mmd`

**Finding.** The file holds bare mermaid source with a `.mmd` extension, so GitHub renders
it as a paragraph of text. `hermes-agent` and `trace-eval` were converted to fenced `.md`
files for this reason. Impact is smaller here because that README embeds the same diagram
inline and links a generated `architecture.svg`, so no reader is stranded.

**Fix.** Same shape as the other two: create `examples/e2e-agent/architecture.md` with a
title, the diagram inside a ` ```mermaid ` fence, and a short "Reading it" section; delete
the `.mmd` after confirming the fenced content matches; link it from the example's README.

Check first whether anything generates `architecture.svg` from the `.mmd` — the e2e README
says the SVG is "auto-generated on PR", and no workflow in the repository does that today,
so that claim needs correcting or the generator needs restoring.

**Verify.**

```bash
# This document names the .mmd file six times, so it has to be excluded or the check can
# never pass. Expect no output.
grep -rn "\.mmd" --include="*.md" --include="*.yml" . \
  | grep -v node_modules | grep -v "docs/REPO-AUDIT.md"
test ! -f examples/e2e-agent/architecture.mmd && echo "converted"
```

### Task 16 — Drop the obsolete Compose `version` key

**Finding.** `version: '3.8'` sits at line 1 of **both** Compose files in the repository:
[`examples/e2e-agent/docker-compose.yml`](../examples/e2e-agent/docker-compose.yml) and
[`examples/rag-langchain/docker-compose.yml`](../examples/rag-langchain/docker-compose.yml).
Compose v2 ignores the key and warns on every invocation.

**Fix.** Delete line 1 of each file. While in the e2e file, consider whether
`volumes: ["./:/app"]` should stay — it bind-mounts the source over the image, which is
convenient for development and means the container writes audit artifacts straight into the
working tree, which Task 3 now ignores but which is still surprising.

**Verify.**

```bash
grep -rn "^version:" examples/*/docker-compose.yml   # expect no output
for f in examples/e2e-agent examples/rag-langchain; do
  docker compose -f "$f/docker-compose.yml" config >/dev/null && echo "$f: no warnings"
done
```

---

## Definition of done

Run all of it. Every line should pass before this document is marked complete.

```bash
# Legal
test -f LICENSE || echo "FAIL: no LICENSE"

# Links across every markdown file.
#
# Fenced blocks are stripped before matching. This document quotes replacement markdown
# destined for the root README and the architecture doc, and those links are relative to
# *their* future homes, not to docs/. Scanning inside fences reports 23 breakages that are
# not breakages and buries any real one.
python3 - <<'EOF'
import re, pathlib, urllib.parse

FENCE = re.compile(r"^\s*(```|~~~)")

def prose_only(text):
    out, in_fence = [], False
    for line in text.splitlines():
        if FENCE.match(line):
            in_fence = not in_fence
            out.append("")
            continue
        out.append("" if in_fence else line)
    return "\n".join(out)

files = [p for p in pathlib.Path(".").rglob("*.md")
         if ".git/" not in str(p) and "node_modules" not in str(p)]
bad = []
for p in files:
    for m in re.finditer(r"\[([^\]]*)\]\(([^)]+)\)", prose_only(p.read_text(errors="replace"))):
        href = m.group(2)
        target = urllib.parse.unquote(href.split("#")[0])
        if href.startswith(("http", "#", "mailto")) or not target:
            continue
        if not (p.parent / target).resolve().exists():
            bad.append((str(p), href))
print(f"{len(files)} md files, {len(bad)} broken links")
for b in bad:
    print("  ", b)
EOF

# Every test suite
python3 -m unittest discover -s tests                          # expect 68
for d in infra/terraform-{aws,azure,gcp}/tests infra/terraform-{aws,azure,gcp}/src/tests; do
  python3 -m unittest discover -s "$d" 2>&1 | grep -E "^(Ran|OK|FAILED)"
done

# Terraform
terraform fmt -check -recursive infra/
for d in infra/terraform-*/envs/*/; do
  terraform -chdir="$d" init -backend=false -input=false >/dev/null && terraform -chdir="$d" validate
done

# Packages
for t in aws azure gcp; do infra/terraform-$t/src/build.sh; done

# Nothing dirty after running the examples
python3 examples/hermes-agent/agent.py --quiet "summarize incident-2291" >/dev/null
python3 examples/trace-eval/eval.py >/dev/null
git status --short   # expect empty
```

Expected end state: **68 example tests + 168 infra tests = 236 passing**, 7/7 Terraform roots
valid, 3/3 build scripts passing, 0 broken links, clean working tree, and a LICENSE.

---

## Appendix — verified healthy at audit time

Checked and found correct, listed so this document is not read as a list of everything
examined.

| Check | Result |
|---|---|
| Relative links across 67 markdown files (prose, outside code fences) | 0 broken |
| `terraform fmt -check -recursive`, all three trees | clean |
| `terraform validate`, all 7 roots — re-checked on 1.15.8; CI pins 1.9.8 | 7/7 pass |
| Write-boundary suites (AWS 11, Azure 3, GCP 11) | 25/25 pass |
| Handler suites (AWS 63, Azure 41, GCP 39) | 143/143 pass |
| Example suites (hermes-agent 31, trace-eval 35) | 66/66 pass |
| `src/build.sh`, all three trees | all pass |
| Tracked build artifacts, `__pycache__`, `.zip`, state files | none |
| Hardcoded credential-shaped strings | none |
| `python3 -m compileall examples tests` | all compile |

234 tests passed at audit time. The `.gitignore` is thorough on Terraform artifacts and
explains its own reasoning, which is what makes Task 3 stand out — it covers the 580 MB
failure mode and misses the one that leaks prompt text.

---
---

# Round two — 2026-08-15

A second pass, one day after the first. Everything above this line is the record of
2026-08-14 and is left exactly as it was written; nothing in round one was edited to
accommodate what follows. An audit that gets revised after the fact stops being evidence of
what was true when it ran.

**What changed in between.** The [hardening plan](HARDENING-PLAN.md) landed its first two
phases — example syntax and import verification, and Dependabot. The
[concepts plan](CONCEPTS-PLAN.md) added harness, context, and graph engineering, taking the
repository from eight examples to eleven and from 68 tests to 146.

**How these findings were reached.** Round one was a full read. This one is narrower: it comes
from working in the repository for a day and noticing what the checks do not cover. Three of
the six are consequences of the repository growing — the fourth is stale text in a document
written yesterday.

**Scope:** 11 examples, 146 tests, 3 Terraform trees, 2 workflows, 70 markdown files.

---

## Progress

| # | Task | Severity | Status |
|---|---|---|---|
| 17 | Documentation changes run no CI at all | high | [x] |
| 18 | Four examples verified by nothing but syntax and import | medium | [x] |
| 19 | `CONTRIBUTING.md` does not describe the bar the repo holds | medium | [x] |
| 20 | `HARDENING-PLAN.md` says "eight examples"; there are eleven | low | [x] |
| 21 | Terraform providers are floors, not pins — a decision, not a defect | low | [x] |
| 22 | Hardening plan phases 3–6 remain | low | [ ] |

Numbering continues from round one deliberately. Task 17 is the seventeenth thing this
repository has been asked to fix, and restarting at 1 would hide that.

---

## Task 17 — Documentation changes run no CI at all

**Severity: high.** The largest structural hole currently in the repository.

Both workflows filter on the same three paths:

```yaml
paths:
  - "infra/**"
  - "examples/**"
  - "tests/**"
```

Nothing matches `docs/**` or the root `*.md` files. This repository is **70 markdown files
against 11 examples** — mostly documentation, by volume and by purpose — and a documentation-only
commit currently merges with zero checks run against it.

This is not hypothetical. Round one, Task 12 in this very document, fixed two broken links in
`REPO-AUDIT.md` pointing at `terraform.yml`, a workflow that had been renamed to `checks.yml`.
A link check would have caught it at review time. There was no link check, and there still is
not one.

**Fix.** Land the link checker used to verify both plans into `.github/scripts/linkcheck.py`,
add a `docs` job to `checks.yml`, and widen both workflows' path filters to include `docs/**`
and `*.md`.

Two things the checker must handle, both established by writing a naive version and reading
its output — it reported 34 broken links across this repository and every one was a false
positive:

- **Fenced code blocks.** This document and both plans quote other files' markdown, including
  their relative links, inside triple-backtick fences. Those resolve against the file being
  quoted, not the file quoting it.
- **`#fragment` suffixes.** `ARCHITECTURE.md#6--what-terraform-builds` is a valid link to a
  file that exists. Split on `#` and test the left half.

The real count with both handled is zero. This task is about keeping it there.

**Verify:**

```bash
python3 .github/scripts/linkcheck.py .          # exits non-zero on the first broken link
python3 -c "
import yaml
w = yaml.safe_load(open('.github/workflows/checks.yml'))
assert 'docs/**' in w[True]['pull_request']['paths'], 'docs still not covered'
print('docs changes now trigger CI')"
```

---

## Task 18 — Four examples verified by nothing but syntax and import

**Severity: medium.**

`langchain-agent`, `rag-faiss`, `rag-langchain`, and `ray-orchestrator` have no test file. The
`example-deps` job imports them, which catches a stale pin — the failure that actually happened
here — and `compileall` catches a syntax error. Neither catches wrong behaviour.

Seven of eleven examples now have suites. These four are the remainder, and they are the same
four that were quietly broken before round one.

**Fix.** `rag-faiss` is the tractable one and should go first: build an index over a small fixed
corpus, query it, assert the expected document ranks first. Deterministic, offline, no key —
which is what makes it safe to gate merges on. It needs `faiss-cpu` and
`sentence-transformers`, so the suite skips when they are absent and runs in `example-deps`,
the same pattern as `tests/test_e2e_agent.py`.

`ray-orchestrator` is second: assert the tasks fan out and results come back in the right shape.

`langchain-agent` and `rag-langchain` are hardest to test honestly because their subject is a
call to a model. Assert what does not need one — that the chain composes, that the prompt
template renders with the expected variables — and say plainly in the README that the model
call itself is unverified. A test that mocks the model and asserts the mock was called proves
nothing.

`tests/test_agent.py` was renamed to `tests/test_starter_agent.py` as part of this task, so
that every suite matches the `test_<example>.py` convention that `CONTRIBUTING.md` now states.
Round one's prose still refers to the old name — correctly, since that was its name then — and
only the link target was repointed.

That rename immediately broke a relative link in round one, and the `docs` job added in Task 17
caught it on the first run. Worth recording: the check justified itself within the same session
it was written.

**Verify:**

```bash
python3 -m unittest discover -s tests 2>&1 | tail -3
for d in examples/*/; do
  n=$(basename "$d")
  ls tests/ | grep -q "${n//-/_}" || echo "no suite: $n"
done
```

---

## Task 19 — `CONTRIBUTING.md` does not describe the bar the repo holds

**Severity: medium**, and the highest-leverage document in the repository for what it costs.

The current text says "follow PEP8", "add tests or a smoke-check where applicable", and "keep
code simple and dependency-light". None of that is wrong. All of it is generic, and someone
following it would not produce anything resembling `hermes-agent` or `harness-agent`.

The standard this repository actually holds is specific and unusual, and it is currently
written down nowhere:

| The real rule | Where it is visible |
| --- | --- |
| Standard library only, unless the dependency *is* the subject | 7 of 11 `requirements.txt` files, each explaining why |
| Boundary tests are mutation-tested, not trusted | `hermes-agent`, `harness-agent` (9 mutations, all caught) |
| A worked example carries an `architecture.md` with mermaid | `hermes-agent`, `trace-eval`, `e2e-agent`, `harness-agent` |
| No check may require a secret | Every workflow job; stated in `checks.yml`'s header |
| Three tiers — worked, applied, minimal — and new examples declare one | Root README's examples section |
| Comments explain *why*, at the density of the surrounding file | Every `.tf` and `.py` file added since round one |
| Pins are exact, with the resolution date recorded | Every `requirements.txt` |

For a repository whose stated purpose is being read and copied, the file that tells people how
to add to it should not be the least specific document in it.

**Verify:** no command proves this one. The test is whether a contributor reading it could
predict the review comments they would get.

---

## Task 20 — `HARDENING-PLAN.md` says "eight examples"

**Severity: low.** Four occurrences, written yesterday, stale within a day of the concepts work
landing.

Round one's counts in this document are *not* stale and must not be updated — this is a dated
record. `HARDENING-PLAN.md` is a live working document, which is the difference.

**Fix:** update the four occurrences to eleven, and Task 1's title with them.

**Verify:**

```bash
grep -n "eight examples\|eight of the" docs/HARDENING-PLAN.md   # expect no output
```

---

## Task 21 — Terraform providers are floors, not pins

**Decided 2026-08-15: pin to the major.** Recorded here so it stops being re-derived.

The decision was `~>`, not `>=`. A reader running `terraform init` against a floor gets
whatever shipped that morning, which means CI's green check named no version anyone could
reproduce, and the `terraform` entry in `.github/dependabot.yml` opened approximately zero pull
requests — Dependabot raises a constraint only when the constraint excludes the newest release,
and a floor never excludes anything. The accepted cost is that the trees fall a major behind
until someone merges the PR Dependabot now opens.

Constraints as they stand, in every `required_providers` block across the three trees:

| Provider | Constraint | Locked |
|---|---|---|
| `hashicorp/aws` | `~> 5.0` | 5.100.0 |
| `hashicorp/azurerm` | `~> 5.0` | 5.0.1 |
| `hashicorp/azuread` | `~> 3.0` | 3.9.0 |
| `hashicorp/google` | `~> 6.0` | 6.50.0 |
| `hashicorp/random` | `~> 3.6` | 3.9.0 |

**Two things had to be fixed for that to actually be true**, and both had already produced false
findings:

- **Two orphaned tree-level `versions.tf` files** — `infra/terraform-azure/versions.tf` and
  `infra/terraform-gcp/versions.tf` — still carried floors (`>= 3.0`, `>= 5.0`) and
  `required_version = ">= 1.3.0"` against `>= 1.6` everywhere else. Neither is a root, so
  `terraform validate` never reads them and the discrepancy could not fail CI. Dependabot *is*
  pointed at both directories, so the stale floors were also the reason those two entries were
  inert. Both now match their roots. The AWS tree has no equivalent file: it declares in each
  `main.tf`.
- **The AWS lock files were gitignored**, at `infra/terraform-aws/.gitignore` line 5 — not
  merely unstaged, which is what an earlier pass through this concluded from reading only the
  root `.gitignore`. Azure and GCP committed theirs. So the two AWS roots were the only two of
  seven whose provider resolution was unreproducible, which is precisely the thing the pin was
  supposed to guarantee. The rule is removed and both locks are committed; all seven roots now
  carry a tracked lock.

The constraint bounds what `init` may resolve; the lock records what it did. Both halves are
required, and neither substitutes for the other.

**Verify.**

```bash
# No floors left in any required_providers block. Match the bare `version` key, not
# `required_version` — the CLI constraint is `>= 1.6` everywhere and should stay a floor,
# since capping the Terraform CLI to a major buys nothing.
grep -rnE '^\s+version\s*=\s*">=' infra --include='*.tf'   # expect: no matches

# All seven roots carry a tracked lock file
git ls-files 'infra/**/.terraform.lock.hcl' | wc -l        # expect: 7

terraform fmt -recursive -check infra/
```

---

## Task 22 — Hardening plan phases 3–6 remain

**Severity: low.** Tracked in [HARDENING-PLAN.md](HARDENING-PLAN.md), not duplicated here:
`SECURITY.md`, a ruff lint job, `tflint` and `checkov`, and reconciling the Terraform *CLI*
version pin.

Hardening Task 9 is not Task 21 above, though the two have been conflated. Task 21 was about
*provider* constraints and is now closed; hardening Task 9 is about the *CLI* — CI pins 1.9.8,
local development is on 1.15.8, and `required_version = ">= 1.6"` floors both. That one is
still open.

Note that hardening Task 5 and round-two Task 17 are the same work. Task 17 supersedes it and
carries the two false-positive findings that hardening Task 5 was written without.

---

## Definition of done — round two

```bash
python3 .github/scripts/linkcheck.py .
python3 -m unittest discover -s tests 2>&1 | tail -3
python3 -m compileall -q examples/
grep -c "eleven runnable" README.md
```

Task 22 is excluded — it is tracked elsewhere. Task 21 carries its own verify block above.
