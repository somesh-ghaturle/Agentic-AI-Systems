# Next phases plan

The open work list after the 2026-11-16 review: what to fix now, what could be better, and what
phase 2 and phase 3 would add. [ENHANCEMENT-PLAN.md](ENHANCEMENT-PLAN.md) is the record of what
was already done; [ROADMAP.md](../ROADMAP.md) is the direction. This file is the queue between
them.

**Status values.** `Done` — changed in the tree and checked. `Needs maintainer` — a GitHub
setting or a public action that only the repository owner should take. `Open` — not started.
`Declined` — looked at and deliberately not done, with the reason.

**Scope of the review.** Repository structure, the root documents, CI, Dependabot, the
Dockerfiles, and the GitHub settings. The Terraform modules and the architecture chapters were
not read line by line, so nothing here is a finding about the infrastructure code itself.

## Fix now

| ID | Item | Status |
| --- | --- | --- |
| F1 | Protect `main` | Needs maintainer |
| F2 | Dependabot coverage gaps | Done |
| F3 | Published image runs as root, with no SBOM or provenance | Done |
| F4 | `uv.lock` is an empty stub | Done |
| F5 | ROADMAP says 5 decision records, there are 4 | Done |
| F6 | `REPOSITORY-DISCREPANCIES.md` reads as current but is stale | Done |
| F7 | No GitHub Release and no changelog | Changelog done; release needs maintainer |
| F8 | Discussions are advertised but disabled | Needs maintainer |

### F1 — Protect `main`

The repository's thesis is that no change lands without an approval, and `main` accepts a
direct push. In **Settings → Rules → Rulesets**, add a ruleset for the default branch that
requires a pull request and requires the `checks` workflow's jobs to pass. Leave required
approvals at zero while there is one maintainer — GitHub does not let an author approve their
own pull request, so one required approval would block every merge.
[`CODEOWNERS`](../.github/CODEOWNERS) is in place for the day a second reviewer exists.

### F2 — Dependabot coverage gaps

[`dependabot.yml`](../.github/dependabot.yml) now also watches:

- Terraform providers in the Azure modules, the Snowflake tree and the hybrid POC. The old
  comment said the Azure modules declared no `required_providers`; all twelve do now.
- The two npm manifests: `examples/hermes-dashboard/frontend` and `scripts/diagram-gif`.
- `tests/requirements.txt`, grouped with the service it mirrors.

**Declined: a Docker entry.** The base images are `python:3.x-slim` tags, which already float
on patch releases, and the minor version each names is a documented floor. Dependabot would
only propose minor bumps that have to be refused. Pinning images by digest is the real fix and
is listed under phase 2.

### F3 — Published image

[`services/trace-eval-service/Dockerfile`](../services/trace-eval-service/Dockerfile) now runs
as uid 10001, and so do the `rag-langchain` and `starter-agent` example images.
[`publish-image.yml`](../.github/workflows/publish-image.yml) attaches an SBOM and a build
provenance attestation on push.

**Not verified locally:** Docker was not running when this was changed, so none of the three
images was built. The publish workflow's own smoke test builds the service image and calls
`/healthz` before pushing, and will catch a break there; the two example images have no such
check. Build them once before the next release:

```bash
docker build -t rag-langchain-check examples/rag-langchain
docker build -t starter-agent-check examples/starter-agent
```

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

[`CHANGELOG.md`](../CHANGELOG.md) exists and covers `0.1.0` and the unreleased changes. The
release itself is the maintainer's call, because pushing a `v*` tag publishes an image:

```bash
git tag v0.2.0 && git push origin v0.2.0
gh release create v0.2.0 --title "v0.2.0" --notes-file CHANGELOG.md
```

Also create a Release for the existing `v0.1.0` tag, so the first version is not tag-only.

### F8 — Discussions

The README offers prompts for GitHub Discussions and the feature is off.

```bash
gh repo edit --enable-discussions
```

## Can be better

| ID | Item | Status |
| --- | --- | --- |
| B1 | README length: move the CI section out | Done |
| B2 | OWASP link pointed at the web Top Ten | Done |
| B3 | No pull request template, CODEOWNERS, or root `CLAUDE.md` | Done |
| B4 | Model defaults span generations | Open |
| B5 | GIF weight in git | Open — see P2.4 |
| B6 | External links are never checked | Open |
| B7 | Local branch clean-up | Needs maintainer |

### B1 — README length

The CI section moved to [CI.md](CI.md); the README keeps a four-line summary. The count
checks that pointed at the README now point at `CI.md`.

### B4 — Model defaults

AWS and GCP default to `claude-opus-5`. The Snowflake defaults name `claude-sonnet-4-5` and
the Azure defaults name `gpt-4o`. Whether those two are still offered by Cortex and Azure
OpenAI was **not checked** in this review. Action: confirm availability and retirement dates,
then either bump the defaults or record in the tree's README why the older model is kept. The
Azure choice is governed by
[ADR 0002](DECISION-LOGS/0002-azure-openai-vs-claude.md), so a vendor change goes through a
new record, not an edit.

### B6 — External links

`linkcheck.py` excludes external URLs on purpose, because a network check in a pull request
fails for reasons unrelated to the change. A weekly scheduled job that only opens an issue
keeps that property and still finds dead links. The wrong OWASP link (B2) sat in the README
because nothing looks.

### B7 — Local branches

Twenty-one local branches are already merged into `main`. `git branch --merged main` lists
them; delete what is no longer needed.

## Phase 2 — make it adoptable

The gap today is not correctness. The repository has no stars, no forks, no release and no
homepage, and nothing shows any tree has ever been applied.

| ID | Item | Why |
| --- | --- | --- |
| P2.1 | Evidence of one real apply | A reader cannot tell a validated tree from an applied one |
| P2.2 | Remote state bootstrap | Every tree applies against a local, unbacked-up state file |
| P2.3 | Azure execution-state recovery | Named in `HOW-TO-RECOVER.md` as having no recovery path |
| P2.4 | GitHub Pages for the interactive diagrams | Removes GIF weight and fills the empty homepage |
| P2.5 | Release `v0.2.0` | Follows F7 |
| P2.6 | Pin container base images by digest | The fix F2 declined to fake |
| P2.7 | Build the example images in CI | F3 could not be verified without it |

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

1. F1, F8, and B7 — settings and clean-up, a few minutes.
2. Build the two example images (F3), then tag and release (F7, P2.5).
3. B4 — verify the model defaults.
4. P2.4, because it also fixes discoverability.
5. P2.2 and P2.3, then P2.1 as an ADR.
6. Phase 3 in table order.
