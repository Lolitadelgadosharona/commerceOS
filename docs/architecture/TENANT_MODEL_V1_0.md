# Commerce OS Tenant Model v1.0

Status: minimal V1 scope with future-compatible identifiers

## V1 assumption

V1 supports one accountable owner/operator and one active `Organization`. It is a single-tenant product deployment, not a multi-tenant SaaS platform. There is no tenant switching, organization marketplace, cross-organization analytics, delegated reseller administration, or tenant billing in V1.

The single-operator assumption simplifies user experience and deployment but does not permit global/unscoped business data. Every canonical business record still carries an immutable `organization_id`, and project-relevant records carry `project_id` where applicable. Authorization derives scope from the authenticated session/service policy rather than accepting an arbitrary client-supplied organization.

## Scope hierarchy

```text
Organization
├── Brand
├── Store
└── Project
```

- `Organization` is the top-level legal/authority/data boundary.
- `Brand` is a commercial identity and policy/presentation boundary.
- `Store` is a commerce surface/account, normally associated with one brand.
- `Project` is a bounded initiative/work context and may reference a brand/store or be organization-wide.

V1 may provision one default Brand, Store, and Project when the workflow needs them. Defaults are real records with typed IDs, not null/global shortcuts.

## Future compatibility without V1 overengineering

- Use opaque stable IDs and organization-scoped unique constraints from the first schema.
- Include `organization_id` in authorization, events, audit, storage prefixes, idempotency scope, and provider-connection ownership.
- Do not build tenant discovery, switching, cross-tenant sharing, per-tenant infrastructure, metering, or tenant lifecycle automation in Phase 1.
- Avoid database row-level-security dependence in the logical contract; the implementation may add defense-in-depth later.
- Never infer organization from email domain, provider account, Brand, Store, or Project alone.
- Cross-organization identity linking and data movement are prohibited until a separately approved multi-tenant privacy/security design exists.

## V1 invariants

One active Organization is configured; each user/service has explicit organization scope; every request/event is checked against that scope; every external connection belongs to the Organization; every export/deletion/retention action is scoped; and missing/mismatched scope fails closed.
