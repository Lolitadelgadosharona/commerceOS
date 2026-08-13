# Sprint 034 Completion Notes

Status: implementation complete; local validation passed

## Delivered

- Added expiring, revocable, opaque bearer sessions backed by stored token digests.
- Added login, logout, and current-actor endpoints using existing Argon2id credentials.
- Added universal protected-route authentication, explicit organization validation, RBAC checks, and domain authorization composition.
- Removed `X-Actor-ID` from the production identity path while retaining an explicit test-only compatibility helper.
- Added an explicit worker runtime principal and documented future initiating-actor propagation.
- Added security audit documentation and focused authorization, revocation, tenant, permission, and audit tests.

## Authority preservation

- Governance remains the authority owner.
- Existing RBAC and approval workflow services remain authoritative.
- Self-approval and service-principal approval remain prohibited.
- Authentication grants identity only; it grants no execution or human approval authority.

## Persistence

- Migration `0034_production_auth` adds `auth_sessions` after `0032_strategic_accounts`.
- The migration seeds `api.read` and `api.write`; role grants remain explicit and deny-by-default.
- Session tokens are never persisted in plaintext.
- No commerce entity or workflow is changed.

## Validation evidence

- Ruff formatting and lint passed across 368 files.
- mypy passed across 186 source files.
- Pytest passed: 97 tests.
- Markdown structure and relative links passed across 92 files.
- Python and npm dependency audits found no known vulnerabilities.
- Next.js production build and Playwright passed.
- Docker Compose built and started PostgreSQL, Redis, API, worker, and web; health checks passed.
- PostgreSQL migration downgrade/upgrade and schema comparison passed at `0034_production_auth`.
- GitHub Actions evidence is pending branch publication.
