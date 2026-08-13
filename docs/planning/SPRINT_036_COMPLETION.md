# Sprint 036 Completion Notes

Status: implementation and validation complete

## Delivered

- Hardened the existing Intelligence connector registry instead of creating a competing source of truth.
- Added provider-neutral capability, authentication state, credential reference, rate-limit metadata, and controlled lifecycle fields.
- Added generic ingestion states, timing, counts, and sanitized structured errors.
- Added canonical SHA-256 evidence identity, idempotent capture, and immutable raw records.
- Added language, source occurrence, relevance metadata, and bounded-confidence normalization fields.
- Added Governance audit records for connector, ingestion, capture, and normalization mutations.

## Authority preservation

- External records remain evidence owned by Intelligence.
- No connector or normalization record creates an opportunity, product, customer, campaign, decision, or approval.
- Sprint 035 AI Runtime is not invoked automatically and retains no source-truth authority.
- No external source call or autonomous behavior is added.

## Persistence and API

- Migration `0036_external_connectors` extends four existing connector/evidence tables.
- The migration safely backfills existing records and adds database-enforced raw-evidence immutability.
- Existing `/api/v1/connectors`, `/market-data-records`, `/normalized-market-items`, and `/ingestion-jobs` APIs expose the hardened contracts.

## Validation evidence

- Ruff formatting and lint: passed (382 files)
- mypy: passed (193 source files)
- pytest: passed (105 tests)
- documentation validation: passed (96 Markdown files)
- Python and npm dependency audits: passed; no known vulnerabilities
- Next.js production build and Playwright: passed
- Docker Compose: API, PostgreSQL, Redis, worker, and web healthy/running
- PostgreSQL migration: downgrade to `0035_ai_runtime`, upgrade to head, current revision, and schema drift check passed
- Security smoke test: unauthenticated connector access rejected with HTTP 401
- GitHub Actions: backend, web, and documentation checks passed on Draft PR #35
