# Sprint 002 — Governance & Identity Foundation Completion

Status: implementation and local runtime validation complete; publication and remote CI pending

## Delivered scope

- Internal `User` principals with normalized email, lifecycle state, human/service classification, and separate Argon2id password credentials.
- `Role`, `Permission`, role-permission, and revocable organization/project-scoped user-role records for Owner, Approver, Operator, and Viewer composition.
- A guard that prevents service principals from receiving human approval authority.
- `ApprovalRequest` with pending, approved, rejected, and cancelled transitions; self-approval is prohibited and decisions require scoped `approval.decide` permission.
- Append-only `AuditLog` persistence; authentication, role changes, and every approval transition produce evidence in the same database transaction.
- External `CustomerIdentity` observations with provider, external identifier, confidence, verification status, and provenance. No connector or automatic identity merge was added.
- Versioned `/api/v1` resources for users, roles, permissions, role assignments, approvals, audit-log reads, and customer identities.
- Alembic revision `0002_governance_identity` with reversible schema and legacy CustomerIdentity backfill.

## Architecture compliance

Governance owns principals, authority, approvals, audit, and identity linking. The implementation is a modular-monolith extension and does not add AI agents, LLM calls, Shopify, advertising, messaging, creative workflows, finance automation, or external integrations. Human authority is explicit; service principals cannot decide approvals. PostgreSQL remains canonical, and all new write workflows use the existing SQLAlchemy transaction boundary.

## Security boundary and known limitations

Sprint 002 implements password verification and authorization primitives, not a production login/session system. `X-Actor-ID` is an internal actor-context placeholder and is not trusted authentication. Bootstrap user creation and permission administration require deployment-level restriction until verified authentication and administrative authorization are added. The API remains prohibited from public deployment. Customer identity records are observations; providers are not contacted and identities are not automatically merged.

## Validation evidence

- Python formatting/lint and strict type checking: passed.
- Pytest: 21 tests passed, covering authentication, RBAC and revocation, approval authority/state changes, audit creation, identity mapping, APIs, existing domains, events, and migrations.
- Alembic: upgrade, schema consistency check, downgrade to Sprint 001, and re-upgrade passed locally.
- Docker Compose: API, PostgreSQL, Redis, worker, and web built and started; API/PostgreSQL/Redis health checks, worker readiness, and web response passed.
- Real PostgreSQL: revision `0002_governance_identity` upgrade, schema consistency, downgrade to `0001_sprint_001`, re-upgrade, and final head verification passed. The first run found a PostgreSQL 63-character constraint-name limit missed by SQLite; the explicit name was shortened and the clean transactional retry passed.
- Redis: readiness command returned `PONG` and the worker reached its intentionally idle foundation state.
- Web: TypeScript lint, production build, Playwright shell test, container start, and HTTP response passed.
- Dependency review: pip-audit and npm audit found no known third-party vulnerabilities; the unpublished local `commerce-os` package is not present in public advisory indexes.
- GitHub Actions: pending branch publication.

## Acceptance mapping

| Acceptance criterion | Status |
|---|---|
| User identity and secure password abstraction | Passed locally |
| RBAC and revocable scoped assignments | Passed locally |
| Approval workflow and human authority controls | Passed locally |
| Approval audit records | Passed locally |
| Customer identity foundation | Passed locally |
| `/api/v1` API | Passed locally |
| Migration round trip | Passed on SQLite and real PostgreSQL |
| Automated tests | Passed locally |
| Docker runtime | Passed for all five services |
| Commit, push, Draft PR, CI | Pending |

## Recommendation

**NOT READY FOR SPRINT 003** until branch publication and remote CI are complete. This recommendation will be updated after those final gates are run.
