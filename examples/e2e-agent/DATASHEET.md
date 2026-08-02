# Dataset Datasheet — E2E Agent Demo Inputs

- Dataset name: e2e-agent-demo-inputs
- Version: v0.1.0-demo
- Date created: 2026-08-02
- Owners / Contacts: Platform Team (example)

## Summary

- Short description: Small synthetic corpus of example prompts and scenario inputs used to exercise the E2E demo. Not representative of production data.
- Size and format: ~10-100 short text prompts stored as JSON lines for CI smoke checks and local testing.

## Collection Process

- How data was collected: Hand-authored synthetic examples created by maintainers for demonstration purposes.
- Sampling strategy: N/A for synthetic dataset.
- Consent and legal basis: N/A (synthetic).

## Preprocessing

- Cleaning/normalization: Basic trimming and UTF-8 normalization.
- Anonymization: N/A — synthetic data contains no PII.

## Composition

- Fields: `prompt` (string), `intent` (string label, optional), `created_by` (string), `created_at` (ISO timestamp).
- Sensitive attributes: None.

## Uses & Limitations

- Recommended uses: CI smoke tests, local demos, architecture validation.
- Known biases or limitations: Synthetic prompts do not reflect real-world distribution and should not be used to benchmark production models.

## Maintenance

- Update cadence: As examples or coverage needs change.
- Provenance: Stored in repo history; production datasets require immutable snapshots and lineage tracking.

## Access & Licensing

- Access: Public within repo; in production, apply access control.
- License: MIT (follow project LICENSE)
