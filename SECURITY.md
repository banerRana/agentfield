# Security Policy

## Supported Versions

The Brain project follows semantic versioning. The latest minor release receives security updates. Patch releases may be issued for critical fixes as needed.

## Reporting a Vulnerability

If you discover a security vulnerability, please send a report to [INSERT SECURITY CONTACT]. Please do not create a public issue. We will acknowledge your report within five business days, and we aim to provide a remediation plan or mitigation strategy within two weeks.

When reporting, include as much detail as possible:

- Steps to reproduce the vulnerability.
- Expected and actual results.
- Any proof-of-concept code, if available.
- Impact assessment (confidentiality, integrity, availability).

We appreciate responsible disclosure and will credit reporters in release notes if desired.

## Disclosure Process

1. We validate the report and assess the severity.
2. We develop and test a fix.
3. We coordinate a release and communicate guidance to affected users.
4. We disclose the issue publicly after a fix or mitigation is available.

## Security Hardening Tips

- Rotate API keys, credentials, and signing keys regularly.
- Run the control plane behind TLS-terminating proxies or service meshes.
- Limit network access to the control plane and SDK callback URLs.
- Enable audit logging to capture administrative actions and workflow executions.

