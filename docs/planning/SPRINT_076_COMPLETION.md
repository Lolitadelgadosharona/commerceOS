# Sprint 076 Completion — Governed Shopify Channel Adapter

Status: implemented; real merchant connection and real external publication were not performed.

## Delivered

- Tenant-scoped Shopify connection registry with server-only credential references, scope validation and centralized API version.
- Provider-neutral adapter plus deterministic mock and a GraphQL Admin transport boundary.
- Deterministic, version-pinned Approved Listing to Shopify draft projection.
- Backend-owned readiness with explicit blockers, warnings, media, variants and inventory safety.
- Separate request, human approval, authorization and explicit execution stages.
- Idempotent Outbox/Worker create-or-update workflow and persisted external references.
- Read-only drift reconciliation and safe failure classification/retry behavior.
- Shopify Control Center, product detail workflow, Listing integration and Decision Queue relationship.
- Reversible migration `0076_shopify_channel_adapter` and deterministic acceptance tests.

## Boundary

Sprint 076 does not publish a product to a public channel, fabricate inventory, add a webhook receiver, perform OAuth installation, execute customer acquisition, or use a real Shopify credential. These remain explicit follow-up work.

## Priority gaps

- P0 before production: real development-store validation, production OAuth/managed-secret flow, webhook signature validation, operational rollback exercise and production observability.
- P1: rich media ingestion/validation, inventory-source integration, webhook-driven reconciliation and a dedicated Shopify decision detail route.
- P2: additional channel adapters and optimization only after live controlled validation.

