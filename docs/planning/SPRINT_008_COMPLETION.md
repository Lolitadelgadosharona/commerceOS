# Sprint 008 — Listing Intelligence and GEO Foundation Completion

Status: implementation and runtime validation complete; publication validation pending

## Delivered scope

- Product-grounded listing strategies with controlled lifecycle.
- Typed customer question maps with provenance and importance.
- Confidence-scored GEO discovery entities and relationships.
- Version-audited human-authored content briefs.
- Provenanced listing evidence with same-product Product Truth validation for specifications.
- Five `/api/v1` resource families and reversible Alembic revision `0008_listing_geo`.

## Architecture compliance

Product Truth remains authoritative and cannot be changed by listing intelligence. Strategy approval requires existing Product Truth but grants no publication authority. No Shopify, SEO/GEO automation or publishing, listing generator, AI copywriter, LLM, agent, advertising, or external integration was added.

## Validation evidence

- Ruff formatting/lint: passed.
- Mypy strict: passed.
- Pytest: 39 tests passed locally, including model, API, lifecycle, relationship/scope, and migration coverage.
- Documentation/link validation passed across 40 Markdown files.
- Docker Compose started PostgreSQL, Redis, API, worker, and web; all defined health checks passed, API/web responses succeeded, and worker readiness was logged.
- Real PostgreSQL upgraded to `0008_listing_geo`, reported no schema drift, downgraded to Sprint 007, re-upgraded, and finished at the Sprint 008 head.
- Next.js type checking/build and the Playwright foundation test passed.
- pip-audit and npm audit found no known third-party dependency vulnerabilities; the unpublished editable local package is absent from public advisory indexes.
- GitHub publication and remote CI validation: pending.

## Recommendation

**NOT READY FOR SPRINT 009** until runtime migration cycling, Docker health, documentation validation, and remote CI are complete.
