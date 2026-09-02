# Compliance

This repository is a reference implementation for production agentic systems. It is not itself a
live service, a production deployment, or a legal compliance program; it is a set of patterns,
configuration, and examples meant to be copied into a real environment with the appropriate
org-level controls.

The compliance story here is therefore practical rather than legal: the repository documents the
security and governance controls it expects any copied deployment to keep, and it tests that those
controls remain visible in the code.

## What this repository commits to

The repo is organised around one hard rule:

> A state-changing action cannot reach production without a human approving that specific
> action.

The implementation is reflected in the Terraform trees, the example agents, and the CI checks:

- approval tokens are single-use and bound to an action fingerprint
- write tools are separated from read tools in the architecture and examples
- log streams and trace records capture the decision path for audit and debugging
- archive storage is configured with retention and immutability controls in the production
  environments
- CI checks scan for secrets, lint Python, validate Terraform, and assert the repo's security
  invariants remain true

## Scope

This compliance posture covers the repository's implementation boundaries and the controls they are
built to demonstrate:

- write-boundary enforcement in the Terraform trees under `infra/`
- approval-gate examples under `examples/`
- audit and trace emission, including log-retention, provenance, and observability settings
- repo security controls under `.github/`, `SECURITY.md`, and the example test suite
- documentation of the operating assumptions behind the design, including the places where a
  control is intentionally weak or absent by design

It does not cover a real cloud deployment, a live customer dataset, or the legal obligations of a
particular regulator, jurisdiction, or customer environment. Those must be mapped to the specific
system that copies this pattern.

## Required controls

Any deployment that copies this repository should keep the following controls in place:

1. Separation of read and write actions
   - A tool that changes state must require a distinct approval path and never be exposed through
     the same router as a general-purpose read tool.

2. Approval claims must be exact and single-use
   - Approval must bind to the action and arguments, not to a generic "allow this agent" flag.
   - Expired or mismatched claims are rejected.

3. Auditability
   - Each state-changing action should produce a trace or log record showing who approved it, what
     action was proposed, and what decision outcome was reached.

4. Retention and immutability
   - Archive and audit storage should retain evidence long enough to support incident review and
     operational investigation.
   - Where the cloud supports it, apply lock or immutability settings in production.

5. Secret and dependency hygiene
   - Keep credentials out of the repository.
   - Pin dependency versions and scan for secrets and vulnerable workflow patterns.

6. CI as a compliance check
   - The workflows under `.github/workflows/` are part of the repository's evidence chain. If a
     control is documented, the workflow should be able to check it.

## Evidence in this repository

The repository includes working checks for the controls above:

- `tests/test_security_policy.py` asserts example coverage and scope are kept in sync
- `tests/test_tfconstraints.py` ensures provider constraints are pinned consistently
- `tests/test_tool_discovery.py` and related boundary tests guard the write/read split in practice
- `gitleaks` scanning over the repo history checks for inadvertent secrets
- Terraform validation and Python linting run without cloud credentials under `.github/workflows/`

These checks are intentionally deterministic and offline. They are evidence of the repository's
claims, not a substitute for a real deployment review.

## Operational note

A project that copies this repository into a production environment should still perform the usual
control mapping for its own jurisdiction and risk profile:

- data classification and retention policy
- access control and least-privilege reviews
- backup and recovery testing
- incident response and ownership
- change-management and approvals for production deployments

This document is not a substitute for legal or regulatory review. It records the engineering
controls the repository implements and the evidence it keeps to support them.
