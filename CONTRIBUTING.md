# Contributing

This repository is reference material. Almost everything in it is read and copied more often
than it is run, which inverts the usual priorities: a subtly wrong example here does not page
anyone, it gets pasted into somebody else's system and fails there instead.

That is the reason for the standards below. They are stricter than the code needs and exactly
as strict as being copied requires.

## The short version

- **Standard library only**, unless the dependency *is* the subject of the example.
- **Pin exact versions**, and record the date they resolved.
- **No check may require a secret**, a network, or a cloud account.
- **A boundary is not tested until you have broken it** and watched a test go red.
- **Comments explain why, not what** — at the density of the file you are editing.

## Examples

New examples go in `examples/` and declare a tier. The root README groups them this way and the
tier sets the bar.

| Tier | What it is | What it must carry |
| --- | --- | --- |
| **Worked** | The full treatment of one idea | Package layout, `architecture.md` with mermaid, a test suite in `tests/`, mutation-tested invariants |
| **Applied** | An idea in a realistic setting | Tests, plus whatever governance documents the setting implies |
| **Minimal** | One idea, one script | A README that says what it demonstrates and what it simplifies |

[hermes-agent](examples/hermes-agent/README.md) and
[harness-agent](examples/harness-agent/README.md) are the worked examples to imitate.
[context-compaction](examples/context-compaction/README.md) is a good minimal one.

### Dependencies

Seven of eleven examples have an empty `requirements.txt` carrying only a comment explaining
why. Match that. The question is not "would a framework be convenient here" but "is the
framework the thing being demonstrated":

- [graph-agent](examples/graph-agent/README.md) depends on LangGraph, because a graph example
  that hand-rolls its own graph demonstrates the opposite of its subject.
- [harness-agent](examples/harness-agent/README.md) depends on nothing, because a harness is
  the layer you would otherwise get *from* a framework, and importing one would delegate the
  subject away.

When you do add a dependency:

```text
# Pinned rather than floored. Direct dependencies only, at the versions that resolved.
# Resolved 2026-08-15 on Python 3.12.
langgraph==1.2.11
```

Exact pins, the resolution date, and a sentence on why the dependency is there. Then add the
example to the matrix in [`.github/workflows/example-deps.yml`](.github/workflows/example-deps.yml)
so CI installs the pin and imports the module — a pin that is never installed is a pin that
rots silently, which is a failure this repository has already had.

## Tests

Standard library `unittest`. Not pytest — it is in no requirements file here, and tests written
as bare pytest functions were collected by nothing and had never run.

Suites live in `tests/`, named `test_<example>.py`, and are discovered by
`python3 -m unittest discover -s tests`.

**If your example needs dependencies, the suite must skip without them** rather than fail. The
`examples` CI job installs nothing, so a suite that cannot skip breaks the fast signal for
everybody. See [`tests/test_e2e_agent.py`](tests/test_e2e_agent.py) for the pattern.

### Mutation testing

For anything that enforces a boundary — a write gate, an approval, a state transition, a
retention policy — writing a passing test is not enough. Break the invariant, run the suite,
and confirm it goes red.

This is not ceremony. Every one of these was caught this way and would otherwise have shipped:

- A `save` that truncated before serializing, leaving an empty progress file
- A `verify` that advanced state even when the check failed
- A compactor that dropped the system prompt it existed to preserve
- A read/write classifier where `"what is the refund policy"` routed to **write**

Record the mutations you ran in the example's README, as
[harness-agent](examples/harness-agent/README.md) does.

## Documentation

Prose, not bullets, wherever an argument is being made. State the trade-off rather than the
recommendation alone — "X, at the cost of Y" — and say plainly what an example does *not* do.

**Sourcing matters.** [`docs/agentic-system-architecture/REFERENCES.md`](docs/agentic-system-architecture/REFERENCES.md)
separates claims by evidential weight: primary documentation, established practice, practitioner
consensus, and this repository's own framing. If you add a claim, add its row. If you cite a
URL, fetch it first — a fabricated link in a document about provenance is worse than no link.

Diagrams are mermaid, inline in markdown, so GitHub renders them and no build step is needed.
Do not commit `.mmd` files or generated SVGs.

## Infrastructure

The three Terraform trees deploy the same architecture and are kept at parity. A change to one
usually implies a change to the other two — and where they deliberately differ, the difference
is documented with its reason.

Every tree must keep passing `terraform fmt -check` and `terraform validate` on all its
environment roots, and its write-boundary tests. Those tests exist because `terraform validate`
accepts every mistake they catch: in each case the wrong value is a valid value in a valid
attribute.

## CI

Two workflows, both credential-free:

- [`checks.yml`](.github/workflows/checks.yml) — fmt, validate, boundary tests, handler tests,
  package builds, example suites, syntax, and link checking. Fast, no PyPI.
- [`example-deps.yml`](.github/workflows/example-deps.yml) — installs each example's pins and
  imports it. Slower, needs PyPI, fires only on `examples/` and `tests/`.

**A check that needs a secret is a check that gets disabled the first time one expires.** If
your contribution cannot be verified without credentials, that is a signal about the
contribution, not about CI.

Before opening a pull request:

```bash
python3 -m unittest discover -s tests
python3 -m compileall -q examples/
python3 .github/scripts/linkcheck.py .
terraform fmt -recursive -check infra/     # if you touched infra/
```

### Pre-commit hooks

[`.pre-commit-config.yaml`](.pre-commit-config.yaml) runs a subset of the above automatically on
`git commit` — whitespace and end-of-file fixes, YAML syntax, a large-file guard, `py_compile` on
changed Python, and `terraform validate` on the directories whose `.tf` files you touched:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files     # optional: check everything once, up front
```

The hooks are a convenience, not a gate. CI is the authority, and nothing here can be enforced on
a contributor's machine — `git commit --no-verify` skips all of it. Install them because a
two-second local failure beats a four-minute red pipeline, not because the repository requires it.

One trade-off worth knowing before you install: the terraform hook runs `terraform init
-backend=false` in each changed directory, because `validate` needs an initialized working
directory and has no `-recursive` flag. Directories are deduplicated, but a commit spanning several
modules is still slow. If that bites, drop that one hook with
`SKIP=terraform-validate git commit` and let CI cover it.

See [`docs/PRE-COMMIT.md`](docs/PRE-COMMIT.md) for the full hook reference.

## Pull requests

Branch from `main`, keep commits focused, and describe the change, how to run it, and the
trade-off you chose. Architecture changes are worth discussing in an issue first.

Reviews look for the same things this file does: is it reproducible, is it verified, does it
say what it does not do, and would copying it into a real system be safe.
