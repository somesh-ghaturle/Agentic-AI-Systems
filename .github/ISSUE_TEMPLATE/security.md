---
name: Security Report
about: Report a security vulnerability - DO NOT CREATE PUBLIC ISSUES
labels: security
type: issue
---

**⚠️ DO NOT REPORT SECURITY VULNERABILITIES IN PUBLIC ISSUES ⚠️**

Security vulnerabilities in this repository should be reported privately to the maintainers.

---

## How to Report

Please report security vulnerabilities **privately** by:

1. **Email:** Send details to the repository maintainer (check [CONTRIBUTING.md](../../CONTRIBUTING.md) for contact)
2. **GitHub Security Advisory:** Create a private vulnerability report via [GitHub Security Advisories](https://docs.github.com/en/code-security/security-advisories/repository-security-advisories/about-repository-security-advisories)

---

## What to Include

**Required:**
- [ ] Steps to reproduce the vulnerability
- [ ] Impact assessment (what could an attacker do?)
- [ ] Suggested mitigation or fix
- [ ] Affected components (which cloud tree, module, or example)

**Optional but helpful:**
- [ ] Proof-of-concept code (if applicable)
- [ ] Screenshots or logs (redacted of any sensitive data)
- [ ] Proposed patch or fix

---

## In-Scope Vulnerabilities

We are interested in reports related to:

- Write boundary bypasses in any of the three Terraform trees (AWS, Azure, GCP)
- Write boundary bypasses in `examples/hermes-agent/` or `examples/harness-agent/`
- Compromised approval gate implementations
- Supply chain attacks via Terraform modules
- Authentication/authorization flaws in deployed infrastructure
- Information disclosure in audit logs or provenance
- Denial of service via resource exhaustion

---

## Out-of-Scope Vulnerabilities

We are **not** interested in reports related to:

- Theoretical attacks without practical exploitation
- Missing security headers on documentation sites
- Version disclosure (unless it leads to actual exploitation)
- Rate limiting issues on public demos

---

## What NOT to Do

- ❌ Do **not** create a public GitHub issue
- ❌ Do **not** post in GitHub Discussions
- ❌ Do **not** disclose publicly until a fix is released
- ❌ Do **not** share sensitive information (API keys, credentials, etc.)

---

## Response SLA

We will respond to security reports with the following timeline:

| Severity | Initial Response | Resolution Target |
|----------|-----------------|-------------------|
| Critical | Within 24 hours | Within 7 days |
| High | Within 7 days | Within 30 days |
| Medium | Within 30 days | Within 90 days |
| Low | Within 90 days | Next release |

---

## Security Policy

See [SECURITY.md](../../SECURITY.md) for our full security policy, including:
- Scope of security support
- Disclosure policy
- Coordinates disclosure with maintainers

---

**Thank you for helping keep this repository secure.**
