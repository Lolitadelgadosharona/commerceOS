# Sprint 077 Completion — Shopify Connector Hardening

Status: complete; deterministic engineering gate passed on 2026-09-06.

## Scope decision

No real Shopify store or credential was available or required. Sprint 077 validates the governed Shopify connector with deterministic transports and signed fixtures. It performs no external publication and does not expose the local Mac.

## Hardened contracts

- Centralized GraphQL Admin API version and least-scope configuration.
- Safe merchant identity fields from connection validation, without credential exposure.
- Explicit `productSet` create/update mapping fixed to draft status with no inventory quantities.
- Separate readiness, human approval, authorization, explicit execution, Outbox, Worker, external reference, and reconciliation stages.
- Deterministic create, update, idempotency, Commerce OS newer, external drift, missing resource, compensating rollback, rate-limit, retry classification, and tenant tests.
- Raw-body Shopify webhook HMAC verification, idempotent signed fixtures, and metadata-only persistence.
- Human-readable UI states and a dedicated Shopify publication decision detail route.

## Production-readiness classification

- **Engineering gate:** determined by the final local quality and deterministic acceptance results.
- **Real merchant validation:** pending by design; follow `docs/validation/SHOPIFY_REAL_VALIDATION_PLAN.md` later.
- **Production gate:** not ready. Production OAuth, managed secrets, live merchant/schema validation, hosted webhook delivery, production observability, and operational credential rotation remain outside Sprint 077.

`NOT CONFIGURED` is a supported configuration state and does not block Sprint 078 when the engineering gate passes and no internal P0 architecture gap remains.

## Alembic drift

Migration `0077_shopify_connection_identity` is additive and reversible. Historical constraint-name differences are not rewritten; PostgreSQL schema-drift validation is the production-like authority, while any SQLite-only reflection mismatch is documented rather than repaired by altering migration history.

## Validation evidence

- Ruff formatting/lint: pass; mypy: pass across 294 source files.
- Pytest: 301 passed, including 19 dedicated Shopify contract and lifecycle tests.
- Next.js type check/build: pass; Playwright: 133 passed, including the dedicated publication decision view.
- Documentation structure/links: pass across 177 Markdown files before this completion-note update; final validation repeated after documentation completion.
- Python and npm dependency audits: no known vulnerabilities in auditable dependencies.
- PostgreSQL 16: `0077` upgrade, downgrade to `0076`, re-upgrade to `0077`, current-head verification, and autogenerate drift check passed.
- Docker Compose: PostgreSQL, Redis, API, Worker, and Web rebuilt from current source and running; health checks pass, Web returned HTTP 200.
- Credential audit: no Shopify or ZenMux secret patterns in tracked source; API responses omit credential and webhook-secret references; webhook bodies are not stored; Outbox payloads contain publication IDs only.

## Final gates

- **REAL SHOPIFY STORE AVAILABLE:** NO
- **REAL EXTERNAL PUBLICATION:** NO
- **REAL SHOPIFY VALIDATION:** DEFERRED BY DESIGN
- **SHOPIFY ENGINEERING GATE:** PASS
- **REAL SHOPIFY VALIDATION GATE:** PENDING
- **PRODUCTION SHOPIFY GATE:** FAIL / NOT READY

No internal P0 architecture gap remains in the mocked Shopify execution boundary. Sprint 078 is not blocked by the absence of a Shopify store.
