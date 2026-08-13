# Sprint 037 Completion Notes

Status: implementation and local validation complete; GitHub CI pending publication

## Delivered

- Marketplace-specific connector metadata and `read_marketplace_reviews` capability using the Sprint 036 registry.
- Immutable, tenant-scoped, hash-identified Amazon- and Etsy-compatible review evidence.
- Normalized customer voice records with sentiment, topic, customer language, product reference, and confidence metadata.
- Explicit evidence links to existing customer signals, pain clusters, customer-language records, and opportunity evidence.
- Advisory competitive marketplace observations.
- Protected APIs and Governance audit events for all marketplace intelligence writes.

## Authority preservation

- Marketplace data remains Intelligence-owned evidence.
- Normalization creates no automatic conclusion or recommendation.
- Evidence links require an already-existing tenant-scoped target.
- No product, opportunity, decision, listing, campaign, customer action, external call, or autonomous behavior is created.

## Validation evidence

- Ruff formatting and lint: passed (390 files)
- mypy: passed (197 source files)
- pytest: passed (110 tests)
- documentation validation: passed (98 Markdown files)
- Python and npm dependency audits: passed; no known vulnerabilities
- Next.js production build and Playwright: passed
- Docker Compose: API, PostgreSQL, Redis, worker, and web healthy/running
- PostgreSQL migration: downgrade to `0036_external_connectors`, upgrade to head, current revision, and schema drift check passed
- Security smoke test: unauthenticated marketplace evidence access rejected with HTTP 401
- GitHub Actions: pending Draft PR publication
