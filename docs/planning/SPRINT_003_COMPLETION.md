# Sprint 003 — Customer Intelligence Foundation Completion

Status: implementation, runtime validation, publication, and remote CI complete

## Delivered scope

- Organization-scoped `SignalSource` registry for the eight specified channel types without connector behavior.
- `CustomerSignal` with source lineage, optional in-scope customer reference, closed classification taxonomy, sentiment, severity, confidence, and content reference.
- `CustomerVoiceCluster` with explicit membership, deduplicated derived count, deterministic default severity, and supplied trend direction.
- `CustomerInsight` with explicit evidence membership, derived evidence count, supplied business interpretation/action, impact, and lifecycle status.
- `SignalService`, `ClusterService`, and `InsightService` with tenant/source validation and no AI generation.
- Versioned API resources and reversible Alembic revision `0003_customer_intelligence`.

## Architecture compliance

Intelligence owns the new aggregates and uses only the shared database/session and tenant-reference boundary. Operations remains canonical for customers. Evidence membership is explicit and reproducible. No provider API, connector, scraping, LLM, embedding, AI summary, automation, or agent was added.

## Validation evidence

- Ruff formatting/lint: passed.
- Mypy strict: passed.
- Pytest: 25 tests passed, including entities, services, cross-organization rejection, APIs, and migration round trips.
- Documentation/link validation: passed across 30 Markdown files.
- Docker Compose: PostgreSQL, Redis, API, worker, and web started successfully; all defined health checks passed, worker readiness was logged, and API/web host responses succeeded.
- Real PostgreSQL: upgrade to `0003_customer_intelligence`, schema consistency check, downgrade to `0002_governance_identity`, re-upgrade, and final head verification passed.
- Redis readiness returned `PONG`.
- pip-audit and npm audit found no known third-party dependency vulnerabilities; the unpublished local package is not present in public advisory indexes.
- Next.js lint/build and the Playwright foundation test passed.
- GitHub Draft PR #2 created; backend, web, and documentation CI jobs passed.

## Acceptance mapping

| Acceptance criterion | Status |
|---|---|
| Signals and sources stored | Passed locally |
| Clusters and explicit membership stored | Passed locally |
| Insights and explicit evidence stored | Passed locally |
| APIs | Passed locally |
| Migration | Passed on SQLite and real PostgreSQL |
| Automated tests | Passed locally |
| Docker runtime | Passed |
| GitHub Draft PR and CI | Passed |

## Recommendation

**READY FOR SPRINT 004.** Sprint 003 acceptance gates are satisfied. Public deployment remains separately prohibited by the Sprint 002 authentication activation limits.
