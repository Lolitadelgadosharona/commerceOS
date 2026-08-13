# Production Authentication and Authorization Foundation v1.0

Status: frozen for Sprint 034

## Security gap audit

Before Sprint 034, Commerce OS had organization-scoped users, Argon2id password credentials, roles, permissions, revocable role assignments, human/service principal types, approval authority checks, and immutable audit records. Password authentication existed as an internal service. Some governance endpoints accepted `X-Actor-ID`, but that header was unverified. Most API families did not require an authenticated request, resolve an organization from a verified actor, or enforce RBAC at a common boundary. The worker had no executable business work and no named runtime principal.

The missing controls affected every API family: Governance, Finance, Operations, Decision, Build, Growth, Executive, and Intelligence. The only intentionally public runtime endpoint is `/api/v1/health`; `/api/v1/auth/login` is necessarily unauthenticated. OpenAPI documents remain available in local development and must be disabled or access-controlled by production deployment policy.

Sprint 034 adds the `auth_sessions` table and seeds the RBAC permission keys `api.read` and `api.write`. No business-domain migration is required. Existing users and roles are preserved. Operators must explicitly grant these permissions to appropriate roles before those actors can use protected APIs; access remains denied by default.

## Production security boundary

Protected requests pass four controls in order:

1. Authentication verifies an opaque bearer session against its SHA-256 digest, expiry, revocation state, active user, and organization.
2. Organization validation rejects an explicit organization scope that differs from the verified actor. Domain services continue to validate ownership for identifiers whose organization is resolved from persisted resources.
3. RBAC requires `api.read` for safe methods and `api.write` for mutations. Existing scoped/domain permissions and approval checks remain authoritative inside services.
4. Domain authorization preserves source-of-truth, lifecycle, tenant, financial, and human-approval constraints.

`X-Actor-ID` is not read by the production authentication boundary. A test-only application-state bypass can preserve legacy request helpers; it is not enabled by runtime configuration and cannot represent production identity.

## Authentication model

- Login verifies the existing Argon2id password credential for an active user in the submitted organization.
- A cryptographically random opaque token is returned once. Only its SHA-256 digest is stored.
- Sessions expire after eight hours by default and are rejected after expiry, revocation, user deactivation, or organization mismatch.
- Logout revokes the current session immediately.
- The verified session resolves both actor identity and organization context.
- Session bootstrap and initial role grants are administrative provisioning operations, not public API behavior.

## Authorization and authority rules

- Existing RBAC is extended, not replaced.
- Permission checks are deny-by-default and organization scoped.
- Resource-specific tenant and domain checks remain in their owning services.
- Approval services continue to prohibit self-approval.
- Service principals cannot receive or exercise human approval authority.
- Authentication does not grant approval, financial, launch, publishing, or execution authority.

## Worker security context

The current worker performs readiness checks only and identifies itself as `commerce-os-worker`. Any future job contract must carry the service principal, organization, initiating human actor when applicable, and source request/job identifier. Worker actions must be permission checked and audited. A service principal may execute only delegated non-human actions and may never approve a human request.

## Audit requirements

Login success/failure, session creation, logout, role and permission changes, approval decisions, and other sensitive domain mutations use the Governance audit service. Records identify organization, actor type and ID, timestamp, action, resource type and ID, metadata, and result where applicable. Future asynchronous audit records must preserve both the worker identity and initiating actor.

## Remaining deployment controls

This foundation controls application identity and authorization. Internet deployment still requires TLS termination, rate limiting and credential-stuffing protection, restricted production OpenAPI access, secure database/network configuration, centralized secret delivery, monitoring/alerting, backup recovery validation, and an operator runbook for bootstrap, session revocation, and incident response. Cookie sessions are not used; if introduced later, CSRF defenses become mandatory.

## References

- [Security and Privacy Foundation](../governance/SECURITY_AND_PRIVACY_FOUNDATION_V1_0.md)
- [Role Authority Model](../governance/ROLE_AUTHORITY_MODEL_V1_0.md)
- [Domain Ownership Model](../governance/DOMAIN_OWNERSHIP_MODEL_V1_0.md)
- [API Convention](../architecture/API_CONVENTION_V1_0.md)
