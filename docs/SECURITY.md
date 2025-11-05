# Security Reference

This document describes security-oriented configuration, hardening tips, and operational guidance for Brain deployments.

## Identity & Access

- Use short-lived API tokens for SDK clients.
- Rotate secrets regularly via your secrets manager.
- Store signing keys in HSM or cloud key management.
- Enable audit logging for administrative actions.

## Network Topology

- Place the control plane behind a TLS proxy or service mesh.
- Restrict inbound traffic to known CIDR ranges.
- Use mutual TLS between the control plane and managed agents where possible.
- Segment databases and caches into private subnets.

## Data Protection

- Encrypt data at rest (PostgreSQL, Redis, object storage).
- Use database roles with least-privilege credentials.
- Store environment-specific configuration using sealed secrets or parameter stores.

## Dependency Management

- Enable Dependabot or Renovate to track vulnerabilities.
- Pin Go, Node, and Python dependencies in version control.
- Run `go list -m all` and `pip-audit` in the CI pipeline.

## Operational Monitoring

- Export metrics via OpenTelemetry (already wired in `pkg/telemetry`).
- Collect logs centrally (ELK, Loki, etc.).
- Set up alerts for queue backlogs, workflow failures, and API error rates.

## Incident Response

- Document on-call procedures for responding to security alerts.
- Capture control-plane audit logs and SDK access logs.
- Use `SECURITY.md` (root) for disclosure contact and communication steps.

