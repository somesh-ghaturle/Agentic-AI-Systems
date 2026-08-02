# Incident Runbook Template for Model/Agent Incidents

## Purpose

This runbook describes steps to follow when a model or agent incident occurs.

## Triage & Detection

- Detection channels (alerts, user reports, monitoring dashboards):
- Initial classification: severity levels (P0/P1/P2):

## Containment

- Immediate mitigation steps (disable endpoint, revoke keys, reduce traffic):
- Short-term measures to prevent further damage:

## Investigation

- Collect logs: model inputs/outputs (sampled), infra logs, recent deployments.
- Reproduce issue locally or in staging with recorded inputs.
- Identify root cause candidates (data drift, bug, adversarial input, infra failure).

## Remediation

- Rollback criteria and steps (deploy previous model artifact):
- Hotfixes or rule-based mitigations:

## Communication

- Stakeholders to notify (security, legal, product, customers):
- External communication templates (if customer-impacting):

## Post-incident

- Root cause analysis structure and ownership:
- Action items, timelines, and tracking:
- Lessons learned and update to monitoring/controls:
