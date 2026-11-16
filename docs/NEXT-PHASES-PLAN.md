# Next phases plan

The work list after the 2026-11-16 review. The "fix now" and "can be better" items are finished
and recorded here with what was done. Phase 2 and phase 3 are the open plan.
[ENHANCEMENT-PLAN.md](ENHANCEMENT-PLAN.md) is the record of earlier work and
[ROADMAP.md](../ROADMAP.md) is the direction.

**Status values.** `Done` — changed and checked. `Open` — not started. `Declined` — looked at
and deliberately not done, with the reason.

**Scope of the review.** Repository structure, the root documents, CI, Dependabot, the
Dockerfiles, and the GitHub settings. The Terraform modules and the architecture chapters were
not read line by line, so nothing here is a finding about the infrastructure code itself.

## Fix now

| ID | Item | Status |
| --- | --- | --- |
| F1 | Protect `main` | Done |
| F2 | Dependabot coverage gaps | Done |
| F3 | Published image runs as root, with no SBOM or provenance | Done |
| F4 | `uv.lock` is an empty stub | Done |
| F5 | ROADMAP says 5 decision records, there are 4 | Done |
| F6 | `REPOSITORY-DISCREPANCIES.md` reads as current but is stale | Done |
| F7 | No GitHub Release and no changelog | Done |
| F8 | Discussions are advertised but disabled | Done |
| F9 | The `rag-langchain` image did not build | Done |

### F1 — Protect `main`

The repository's thesis is that no change lands without an approval, and `main` accepted a
direct push. A ruleset named `protect-main` now requires a pull request, and blocks force
pushes and deletion of the branch.

Two things it deliberately does not require:

- **An approving review.** GitHub does not let an author approve their own pull request, so one
  required approval would block every merge while there is one maintainer.
  [`CODEOWNERS`](../.github/CODEOWNERS) is in place for the day a second reviewer exists.
- **Status checks.** `checks.yml` has path filters, and a required check that never starts
  leaves a pull request waiting forever. A change that touches only `.github/dependabot.yml`
  or `CODEOWNERS` matches no filter and would be unmergeable. Requiring checks safely needs one job that always runs; that is P2.9.

### F2 — Dependabot coverage gaps

[`dependabot.yml`](../.github/dependabot.yml) now also watches:

- Terraform providers in the Azure modules, the Snowflake tree and the hybrid POC. The old
  comment said the Azure modules declared no `required_providers`; all twelve do now.
- The two npm manifests: `examples/hermes-dashboard/frontend` and `scripts/diagram-gif`.
- `tests/requirements.txt`, grouped with the service it mirrors.

**Declined: a Docker entry.** The base images are `python:3.x-slim` tags, which already float
on patch releases, and the minor version each names is a documented floor. Dependabot would
only propose minor bumps that have to be refused. Pinning images by digest is the real fix and
is P2.6.

### F3 — Published image

[`services/trace-eval-service/Dockerfile`](../services/trace-eval-service/Dockerfile) now runs
as uid 10001, and so do the `rag-langchain` and `starter-agent` example images.
[`publish-image.yml`](../.github/workflows/publish-image.yml) attaches an SBOM and a build
provenance attestation on push.

Checked on 2026-11-16 by building all five images in the tree. The service image answered
`/healthz` as uid 10001; `starter-agent` ran as `nobody`; `rag-langchain` built its index and
answered a query as uid 10001. `e2e-agent` and `edge-agent` were built and not changed.

### F4 — `uv.lock`

Deleted. It was three lines, declared `requires-python >=3.10` against a 3.9 floor, and locked
nothing, while the README called it the locked dev environment. Ruff is pinned in
`checks.yml` and the test dependencies in `tests/requirements.txt`.

### F5 — Decision record count

`ROADMAP.md` now says 4, and [`docs_counts.py`](../.github/scripts/docs_counts.py) checks the
number against `docs/DECISION-LOGS/`, so it cannot drift again.

### F6 — Stale audit

`REPOSITORY-DISCREPANCIES.md` carries a historical banner, the same treatment `REPO-AUDIT.md`
has, and the README no longer describes it as current.

### F7 — Release and changelog

[`CHANGELOG.md`](../CHANGELOG.md) covers `0.1.0` and `0.2.0`. `v0.2.0` is tagged from the
merge of this change, which also publishes the image, and both tags have a GitHub Release.

### F8 — Discussions

Enabled. The README's discussion prompts now have somewhere to go.

### F9 — The `rag-langchain` image did not build

Found while checking F3, and already broken on `main`. The Dockerfile used `python:3.11-slim`
and a Dependabot bump had moved the `numpy` pin to a version that needs 3.12, so
`pip install` failed. Nothing noticed, because `example-deps.yml` installs the pins on 3.12 and
no job builds the image. The Dockerfile now uses 3.12. The class of failure is still open:
see P2.7.

## Can be better

| ID | Item | Status |
| --- | --- | --- |
| B1 | README length: move the CI section out | Done |
| B2 | OWASP link pointed at the web Top Ten | Done |
| B3 | No pull request template, CODEOWNERS, or root `CLAUDE.md` | Done |
| B4 | Model defaults span generations | Done — verified and kept |
| B5 | GIF weight in git | Open — see P2.4 |
| B6 | External links are never checked | Done |
| B7 | Local branch clean-up | Done |

### B1 — README length

The CI section moved to [CI.md](CI.md); the README keeps a four-line summary. The count
checks that pointed at the README now point at `CI.md`.

### B4 — Model defaults

AWS and GCP default to `claude-opus-5`, Snowflake to `claude-sonnet-4-5`, Azure to `gpt-4o`
version `2024-11-20`. Both older defaults were checked against the vendors' documentation on
2026-11-16 and kept:

- **Snowflake.** `claude-sonnet-4-5` is listed for `AI_COMPLETE` and has no deprecation
  notice. Run `SHOW CORTEX BASE MODELS` in the target account before an apply, since the
  catalog differs by region.
- **Azure.** Microsoft's lifecycle page retires `gpt-4o` version `2024-11-20` on 2027-04-14
  and names `gpt-5.1` as the replacement. It works today and has an end date, which makes it
  P2.8 and not a change to make blind: the vendor choice is governed by
  [ADR 0002](DECISION-LOGS/0002-azure-openai-vs-claude.md).

The dates are recorded beside the allowlist in `tests/test_model_pins.py`, where the next
person to change a pin will read them.

### B6 — External links

[`external_links.py`](../.github/scripts/external_links.py) reports links that return 404 or
410, or whose host does not resolve. `external-links.yml` runs it weekly and opens an issue;
it never gates a pull request, which keeps the reason `linkcheck.py` excludes external URLs.
Its first run found two dead links in the README, both now fixed.

### B7 — Local branches

Local branches already merged into `main` were deleted with `git branch -d`, which refuses
anything unmerged. Remote branches were left alone.

## Phase 2 — make it adoptable

The gap today is not correctness. The repository has no stars, no forks and no homepage, and
nothing shows any tree has ever been applied.

| ID | Item | Why |
| --- | --- | --- |
| P2.1 | Evidence of one real apply | A reader cannot tell a validated tree from an applied one |
| P2.2 | Remote state bootstrap | Every tree applies against a local, unbacked-up state file |
| P2.3 | Azure execution-state recovery | Named in `HOW-TO-RECOVER.md` as having no recovery path |
| P2.4 | GitHub Pages for the interactive diagrams | Removes GIF weight and fills the empty homepage |
| P2.6 | Pin container base images by digest | The fix F2 declined to fake |
| P2.7 | Build the example images in CI | F9 was invisible without it |
| P2.8 | Move Azure off `gpt-4o` before 2027-04-14 | The model has a retirement date |
| P2.9 | One always-run CI job, then require it on `main` | F1 could not require checks safely |

P2.5 was the `v0.2.0` release and is done under F7.

**P2.1 — One real apply.** ROADMAP declines `terraform plan` in CI because a check that needs a
secret gets disabled when the secret expires. That objection does not hold for OIDC, which has
no secret. Proposal: one `workflow_dispatch` workflow, federated to a sandbox account, that
runs `plan` on one tree and uploads the output as an artifact. It is never a required check
and never runs on a pull request, so the no-secrets property of `checks.yml` is unchanged.
`apply` stays a human step. This reopens a recorded decision, so it starts as an ADR.

**P2.2 — Remote state.** Each tree already carries a commented-out backend block. Add a small
bootstrap root per tree that creates the bucket or container and the lock, so switching is one
uncomment and not a separate project.

**P2.3 — Azure state recovery.** Soft delete on the storage account protects blobs, not the
Table Storage resource that execution state lives in. Either move that state to Cosmos, which
has point-in-time restore, or add a scheduled export, and update the runbook to match.

**P2.4 — Pages.** The 49 GIFs are 80 MB in plain git, the largest 6.5 MB, and every re-render
adds permanent history. Publish `docs/diagrams/*.html` with GitHub Pages, link each document to
the live viewer, and keep at most the two README GIFs in the tree. Then set the repository
homepage to the Pages URL.

**P2.7 — Build the example images.** Add a matrix job to `example-deps.yml` that runs
`docker build` on each example Dockerfile. It belongs in that workflow because it has the same
trigger and the same cost profile. Update the job count in `CI.md` in the same change.

**P2.8 — Azure model.** Before 2027-04-14, write the ADR that supersedes 0002's model choice,
move the default to the replacement Microsoft names at that time, and check the handler's call
shape against it — task 46 was a pin that the handler beside it could not call.

**P2.9 — A required check.** Add one job with no path filter that waits for the others, or
passes when they were skipped, and require only that job in the `protect-main` ruleset.

## Phase 3 — go deeper on the theme

| ID | Item | Why |
| --- | --- | --- |
| P3.1 | One trace schema across the trees | Lets `trace-eval` grade real traces from any deployed tree |
| P3.2 | A larger evaluation set | Seven hand-written cases show a method, not a result |
| P3.3 | Two-person approval | Strengthens the human gate for the highest-risk writes |
| P3.4 | Approval fatigue | A gate that is clicked through is not a gate |
| P3.5 | Compliance mapping | Makes the evidence model usable in a regulated review |

**P3.1 — Trace schema.** Trace field names differ per tree today because each provider's
queries match different ones. Define one schema (the OpenTelemetry GenAI conventions are the
obvious starting point), add a thin per-tree export that maps onto it, and point
`trace_eval_service` at the result. This is the item that connects the examples to the
infrastructure.

**P3.2 — Evaluation set.** Add an opt-in script that records traces from a real model and
scores them, kept out of CI because it needs a key. Keep the "no benchmark numbers" stance:
publish the cases and the method, not a score.

**P3.3 and P3.4 — The human side of the gate.** A second approver for writes above a declared
risk tier, enforced by the same store primitive that makes the claim single-use. Then an
example of what approval fatigue looks like in the trace — many approvals in a short window,
approvals faster than the proposal can be read — and how to detect it. Neither adds an
automatic approval path; both make the existing one harder to hollow out.

**P3.5 — Compliance mapping.** Extend [COMPLIANCE.md](../COMPLIANCE.md) with a table from each
control to the EU AI Act human-oversight article and the NIST AI RMF function it supports, and
to the test in this tree that demonstrates it.

**Declined: a Kubernetes or fifth-cloud tree.** It adds a tree to keep at parity without
teaching a property the existing four do not.

## Order

1. P2.7 and P2.9 — small CI changes that close the two holes this round found.
2. P2.4, because it also fixes discoverability.
3. P2.2 and P2.3, then P2.1 as an ADR.
4. P2.8, with a hard date of 2027-04-14.
5. P2.6, then phase 3 in table order.
