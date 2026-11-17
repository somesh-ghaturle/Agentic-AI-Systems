# Next phases plan

The work list after the 2026-11-16 review. The "fix now" and "can be better" items and phase 2
are finished and recorded here with what was done. Phase 3 is the open plan, along with one
step of phase 2 that needs a cloud account.
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

It also requires the `gate` check since P2.9. One thing it deliberately does not require, and
one it could not require at first:

- **An approving review.** GitHub does not let an author approve their own pull request, so one
  required approval would block every merge while there is one maintainer.
  [`CODEOWNERS`](../.github/CODEOWNERS) is in place for the day a second reviewer exists.
- **Status checks.** `checks.yml` has path filters, and a required check that never starts
  leaves a pull request waiting forever. A change that touches only `.github/dependabot.yml`
  or `CODEOWNERS` matches no filter and would be unmergeable. Requiring checks safely needed
  one job that always runs, which is what P2.9 added.

### F2 — Dependabot coverage gaps

[`dependabot.yml`](../.github/dependabot.yml) now also watches:

- Terraform providers in the Azure modules, the Snowflake tree and the hybrid POC. The old
  comment said the Azure modules declared no `required_providers`; all twelve do now.
- The two npm manifests: `examples/hermes-dashboard/frontend` and `scripts/diagram-gif`.
- `tests/requirements.txt`, grouped with the service it mirrors.

**Declined at the time: a Docker entry.** The base images were bare `python:3.x-slim` tags,
which float on patch releases, so Dependabot would only have proposed minor bumps that have to
be refused. Pinning by digest was the real fix; P2.6 did that and added the entry with it.

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
no job builds the image. The Dockerfile now uses 3.12, and P2.7 added the job
that builds every image.

## Can be better

| ID | Item | Status |
| --- | --- | --- |
| B1 | README length: move the CI section out | Done |
| B2 | OWASP link pointed at the web Top Ten | Done |
| B3 | No pull request template, CODEOWNERS, or root `CLAUDE.md` | Done |
| B4 | Model defaults span generations | Done — verified and kept |
| B5 | GIF weight in git | Addressed by P2.4, which kept the GIFs and says why |
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

Done on 2026-11-16, with one item that cannot be finished from inside the repository. The gap
this phase was aimed at was not correctness: nothing showed a tree had ever been accepted by a
cloud, state had nowhere safe to live, and the diagrams could only be seen as GIFs.

| ID | Item | Status |
| --- | --- | --- |
| P2.1 | Evidence of one real apply | Workflow and ADR done; **the evidence itself needs a cloud account** |
| P2.2 | Remote state bootstrap | Done |
| P2.3 | Azure execution-state recovery | Done |
| P2.4 | GitHub Pages for the interactive diagrams | Done |
| P2.5 | Release `v0.2.0` | Done under F7 |
| P2.6 | Pin container base images by digest | Done |
| P2.7 | Build the example images in CI | Done |
| P2.8 | Move Azure off `gpt-4o` before 2027-04-14 | Done |
| P2.9 | One always-run CI job, then require it on `main` | Done |

**What "done" means here.** Every change was checked with the tools CI runs: `terraform
validate` on the roots touched, `tflint`, `checkov`, `conftest`, and the test suites. **Nothing
was planned or applied against a real AWS, Azure, GCP or Snowflake account**, because no
credentials were available. The Terraform in P2.2, P2.3 and P2.8 is therefore validated and
not proven, which is the same standing as the rest of the trees and the reason P2.1 exists.

### P2.1 — Evidence of one real apply

[`plan.yml`](../.github/workflows/plan.yml) runs `terraform plan` on one AWS environment root,
by hand, through OIDC with a read-only role, and uploads the output.
[ADR 0005](DECISION-LOGS/0005-opt-in-plan-with-oidc.md) records why the "no plan in CI" rule
was narrowed: OIDC stores no secret, so the objection that a secret expires no longer holds,
while the objection that a check must not depend on an account still does. The workflow is
never a required check and never runs on a pull request. `apply` stays a human step.

**Still open, and only the maintainer can close it.** The workflow is inert until an account
exists for it:

1. In a sandbox AWS account, add GitHub as an OIDC identity provider.
2. Create a role with the AWS-managed `ReadOnlyAccess` policy, trusted only for
   `repo:somesh-ghaturle/Agentic-AI-Systems:environment:plan`.
3. In the repository, create an environment named `plan` and set the variables
   `AWS_PLAN_ROLE_ARN` and `AWS_PLAN_REGION`.
4. Run the `plan` workflow from the Actions tab.

Until that run exists the repository still cannot show that a tree plans. A plan is also not an
apply: quota and create-time limits only appear on apply, which remains out of scope for CI.

### P2.2 — Remote state bootstrap

`infra/terraform-aws/bootstrap/`, `infra/terraform-azure/bootstrap/` and
`infra/terraform-gcp/bootstrap/` each create the versioned, private bucket or storage account an
environment's backend block points at, and print that block filled in. Each is a root of its
own, applied once, so no environment root can destroy the store holding its own state. The
three are in the `validate` matrix, the `tflint` sweep and Dependabot.

- **AWS** — one S3 bucket: versioned, encrypted, public access blocked, TLS-only, 90 days of old
  versions. Locking uses the S3 backend's lock file, which needs Terraform 1.10 or newer; the
  environment sketches now say `use_lockfile` where they said `dynamodb_table`.
- **Azure** — a resource group, a storage account with blob versioning and soft delete on and
  shared keys off, the `tfstate` container, and a data role for whoever applies it.
- **GCP** — one bucket: versioned, uniform access, public access prevented, 30 generations kept.
- **Snowflake** — no bootstrap, because Snowflake offers nothing a backend can use. Its deploy
  guide says to use the bootstrap of whichever cloud hosts the account.

The environment roots still ship on local state; switching is pasting the printed block and
running `terraform init -migrate-state`. That is deliberate: a committed backend block names a
bucket that exists in one account only.

### P2.3 — Azure execution-state recovery

`modules/state` is now a Cosmos DB for Table account where it was a Storage Table. Table
Storage has no soft delete, no versioning and no point-in-time restore, so the old table had no
recovery path in any environment. Cosmos for Table keeps the same data model and client and
adds continuous backup: on in prod, off in dev and staging, because it cannot be disabled once
enabled. [HOW-TO-RECOVER.md](HOW-TO-RECOVER.md) has the restore command.

Three things worth knowing:

- **No handler reads or writes this table.** That was already true. The Logic App keeps its own
  run state, and the table is wired to the tools by environment variable for the handlers a
  copier adds. The variable was renamed from `STATE_STORAGE_ACCOUNT` to `STATE_TABLE_ENDPOINT`.
- **Zone redundancy was not carried over.** Prod's storage account was ZRS. Whether a
  serverless Cosmos account can be zone-redundant in a given region was not verified, so the
  module does not set it.
- **It is a replacement, not a migration.** Applying this to an environment that already has
  the old table destroys that table. Nothing in this tree wrote to it, so nothing is lost
  unless a copier's own handlers did.

The two diagrams that labelled the store were updated and re-rendered.

### P2.4 — GitHub Pages

[`pages.yml`](../.github/workflows/pages.yml) publishes the interactive viewers to
<https://somesh-ghaturle.github.io/Agentic-AI-Systems/>, with an index. Each of the 49 embedded
GIFs now has a link to its live viewer under it, `embed.py` adds that link for new diagrams,
and the repository homepage points at the site.

**Changed from the plan: the GIFs stay.** The plan said to remove all but two. Removing them
would not shrink the repository, since they remain in history, and it would cost the inline
picture a reader scrolling a document relies on. The growth that matters is future re-renders,
and those are now optional: a diagram can change on the site without a new GIF.

### P2.6 — Base images pinned by digest

All five Dockerfiles pin `python:3.x-slim` by digest, and Dependabot has a `docker` entry that
moves the digest. Minor and major Python bumps are ignored there, because the minor each image
names is a documented floor.

### P2.7 — Example images built in CI

`example-deps.yml` builds every Dockerfile and asserts the image does not run as root. This is
the check that would have caught F9.

### P2.8 — Azure model

The default moved from `gpt-4o` `2024-11-20` to `gpt-5.1` `2025-11-13`, the replacement Microsoft
names. This is an amendment to ADR 0002 and not a new record, because the vendor decision is
unchanged. The handler's call shape needed no change: it already sent `max_completion_tokens`
and no sampling parameters. Checked against Microsoft's documentation, not a live deployment;
the one thing not confirmed is whether the handler's default API version `2024-10-21` is
accepted for this model. ADR 0002's amendment says how to override it.

Found on the way: all three Azure `terraform.tfvars.example` files set
`MODEL_DEPLOYMENT = "gpt-4o"` on the `reason` tool. A per-tool value overrides the one the root
wires from the model module, the deployment is named `reasoning`, and a handler calling a
deployment that does not exist gets a 404. The override is removed. The same files also said
the tree had no handler source, which stopped being true when `src/` was added.

### P2.9 — The required check

[`gate.yml`](../.github/workflows/gate.yml) runs on every pull request, waits for every other
check on the commit, and fails if any failed. The `protect-main` ruleset requires it. The other
workflows keep their path filters, so nothing waits on a check that never starts.

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

1. P2.1's last step: configure the sandbox account and run the `plan` workflow once.
2. Phase 3 in table order. P3.1 first, because it is the item that connects the examples to
   the infrastructure.
