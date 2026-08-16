# Governance Checklist for Systematic AI Enterprise

This checklist helps teams prepare models and agentic systems for enterprise adoption.

1. Inventory and Ownership
   - Maintain a model & dataset inventory with owners and contact info.
   - Record model versions, training data snapshots, and dependencies.

2. Model Cards & Datasheets
   - Create a Model Card for every production model (purpose, limitations, metrics).
   - Create Datasheets for datasets describing collection, preprocessing, and biases.

3. Risk Assessment & Approval
   - Perform initial risk assessment (scope, user impact, regulatory considerations).
   - Define approval gates for sensitive use-cases (legal, privacy, security review).

4. Compliance & Documentation
   - Link regulatory requirements (GDPR, EU AI Act, sector-specific rules).
   - Retain documentation for audits (training logs, evaluation notebooks).

5. Deployment Controls
   - Enforce access control and least-privilege for model endpoints and infra.
   - Use canary/blue-green deployments and traffic shaping for new models.

6. Monitoring & Observability
   - Define and collect runtime metrics: latency, error rates, throughput.
   - Track model performance metrics: accuracy, calibration, fairness metrics.
   - Monitor data and concept drift; set alert thresholds.

7. Retraining & Lifecycle
   - Specify retraining triggers (time-based, performance degradation, data drift).
   - Maintain reproducible pipelines for retraining with pinned dependencies.

8. Explainability & Transparency
   - Provide explainability artifacts where applicable (feature attributions, examples).
   - Document known failure modes and mitigation strategies.

9. Incident Response & Rollback
   - Define rollback criteria and automated rollback procedures.
   - Prepare runbooks for model incidents including contact lists.

10. Auditability & Provenance
   - Store provenance: who triggered training/deploy, code commit, data snapshot.
   - Keep immutable logs for audit (access, predictions for sample sets).

Use this checklist as a baseline; extend per your organization's risk tolerance and regulatory environment.
