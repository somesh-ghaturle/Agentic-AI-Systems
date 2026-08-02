# Security Checklist for Agentic AI Systems

Security considerations for deploying agentic and ML systems in enterprise.

1. Secure Development
   - Enforce code review and branch protection.
   - Run dependency scanning and static analysis in CI.

2. Secrets & Credentials
   - Store secrets in a secrets manager (do not commit to repo).
   - Rotate keys regularly and grant minimal scopes.

3. Runtime Isolation
   - Sandbox untrusted code execution and tool integrations.
   - Use container isolation, resource limits, and user namespaces.

4. Network & Infrastructure
   - Use private networks and VPCs for model serving endpoints.
   - Apply network policies and firewall rules limiting egress.

5. Supply Chain & SBOM
   - Produce SBOMs for deployed artifacts and track third-party components.
   - Verify integrity of model artifacts (signatures, checksums).

6. Access Control & Auditing
   - Enforce RBAC for model deployment and data access.
   - Log administrative actions and access to model endpoints.

7. Testing & Fuzzing
   - Include adversarial and abuse-case tests in CI (prompt injection scenarios).
   - Run fuzzing or input sanitation tests for tool connectors.

8. Incident Management
   - Have a security incident response plan specific to model misuse and data leaks.
   - Maintain alerting and playbooks for high-severity events.

9. Privacy-preserving Techniques
   - Consider differential privacy, synthetic data, or secure enclaves where needed.

10. Regular Reviews
   - Schedule periodic security reviews and penetration tests for critical services.

This checklist is a starting point; align it with your organization's security program and standards.