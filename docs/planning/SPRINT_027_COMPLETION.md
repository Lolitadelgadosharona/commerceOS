# Sprint 027 Completion Notes

Status: implementation complete; local and remote validation passed

## Delivered

- Extended the Decision-owned creative brief contract with product, objective, key message, proof requirements, CTA strategy, and confidence while preserving existing consumers.
- Added Build-owned creative asset, sequential asset version, and creative performance observation records.
- Added organization-scoped `/api/v1` create and read endpoints for assets, versions, and performance observations.
- Added migration `0027_creative_assets` with compatible creative-brief backfill and reversible schema changes.
- Added lifecycle, tenancy, precision, lineage, and approval-boundary tests.

## Architecture and safety

- Decision owns recommendations and creative briefs; Build owns artifact records and versions.
- Growth retains future publishing and distribution authority; Finance retains economic truth; Governance retains approvals.
- New assets are draft and pending only. No endpoint generates, publishes, advertises, invokes providers, or grants approval.

## Validation evidence

- Ruff formatting and lint: passed across 308 files.
- mypy: passed across 153 source files.
- Pytest: 81 passed.
- Markdown structure and relative links: passed across 78 files.
- Python and npm dependency audits: no known vulnerabilities.
- Next.js type check and production build: passed.
- Playwright: 1 passed.
- Docker Compose: PostgreSQL, Redis, API, worker, and web started; required health and HTTP checks passed.
- PostgreSQL migration: `0027_creative_assets` upgrade, downgrade to `0026_ai_discovery_listing`, upgrade, current-head, and schema check passed.
- GitHub Actions: backend, docs, and web jobs passed on Draft PR 26.

## Known activation limits

- Asset `source` and metadata are registry references only; no binary storage or provider adapter is included.
- Performance observations are supplied facts with provenance, not live advertising ingestion.
- Authentication remains subject to the repository's documented non-public deployment limitation.
