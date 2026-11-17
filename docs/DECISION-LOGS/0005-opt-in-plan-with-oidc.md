# ADR 0005 — A hand-run `terraform plan` with OIDC, and still no plan in the checks

**Status: Accepted** · Decided 2026-11-16 · Scope: `.github/workflows/plan.yml`, `ROADMAP.md`

## Context

Every check in this repository runs without a cloud credential, and `ROADMAP.md` recorded the
consequence as a decision: no `terraform plan` in CI, because it needs credentials and "a
check that needs a subscription is a check that gets disabled the first time a secret expires."

That left a gap the checks cannot close from the inside. `terraform validate` does not call an
API. A resource name that exceeds a service limit, an argument the service rejects, a data
source that resolves to nothing, a model that is not offered in the region the example names —
all of these validate, lint, and scan clean. The 2026-11-16 review put the cost of that
plainly: nothing in the repository shows that any tree has been accepted by a cloud, so a
reader cannot tell a validated tree from one that plans.

The original objection has two parts, and only one of them still holds:

- **A stored secret expires.** True of an access key in a repository secret. Not true of
  OpenID Connect: the workflow presents a token GitHub signs for that run, and the cloud
  exchanges it for credentials that last minutes. There is nothing stored, so there is
  nothing to rotate and nothing to expire.
- **A check that needs an account gates every pull request on that account.** Still true, and
  still disqualifying. A fork has no account. A contributor's pull request must not be able to
  read one.

## Decision

Add [`plan.yml`](../../.github/workflows/plan.yml): one workflow, started by hand
(`workflow_dispatch`), that assumes a read-only role through OIDC and runs `terraform plan` on
one AWS environment root from empty local state, then uploads the output.

It is not a check. It does not run on a pull request, it is not in the `gate` workflow's
reach, and the `protect-main` ruleset does not name it. `checks.yml` is unchanged and still
runs with no credential.

`apply` remains a human step in a terminal. The workflow must never contain one, and the role
it assumes is read-only so that one could not succeed.

## Consequences

- **The repository can now show evidence, and does not yet.** The workflow exists and is
  inert until someone configures an account: an OIDC provider, a read-only role trusted for
  the `plan` environment of this repository, and two repository variables. Until then it
  fails at its first step with a message saying what is missing. This record does not claim a
  tree has been planned.
- **A plan is not an apply.** It proves the provider accepts the configuration and can resolve
  everything it reads. It does not prove a resource can be created — quota, service limits
  enforced at create time, and eventual-consistency failures between resources all appear only
  on apply. The gap is narrower, not closed.
- **AWS only.** One tree is enough to establish the pattern and each further tree is another
  federation to set up. Azure and GCP both support the same exchange; adding them is a choice
  list entry and a credentials step, not a new decision.
- **The example variables are what gets planned.** `terraform.tfvars.example` is the file the
  deploy guide tells a reader to copy, so a plan that fails on it is a finding about the
  repository and not about the account.
- **A third-party action enters the repository** (`aws-actions/configure-aws-credentials`),
  pinned by commit SHA like the other two.

## Alternatives considered

1. **Keep the absolute rule.** No workflow touches an account, ever. Rejected: the rule was
   protecting two properties, and this keeps both. What it gives up is only the ability to
   find the class of error that `validate` cannot see.
2. **Plan on every pull request with OIDC.** Rejected for the second reason above. It would
   also make an outage in one cloud a red build for an unrelated change.
3. **Plan against a mock such as LocalStack.** Rejected: it tests the mock's model of the API.
   The errors this is meant to find are precisely the ones where the real service disagrees
   with a model of it.
4. **Commit a plan output by hand, once.** Rejected as the mechanism, though it is how the
   first evidence may well arrive: a file with no workflow behind it goes stale on the next
   provider bump and nothing says so.

## What would reopen this

The workflow being wired into a required check, or gaining an `apply`. Either one changes what
this record decided, and should be a new record and not an edit to the workflow.

Also: a year passing with the account never configured. A capability nobody uses is a claim
the repository makes and does not test, which is the failure this repository keeps naming.
