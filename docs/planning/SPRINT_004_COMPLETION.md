# Sprint 004 — Opportunity Intelligence Foundation Completion

Status: implementation and runtime validation complete; publication and remote CI pending

## Delivered scope

- Intelligence-owned `MarketOpportunity` observations with typed triggers, lifecycle, timing/geography, and confidence.
- `OpportunityEvidence` with supported future source taxonomy and same-organization customer-signal validation.
- Non-authoritative `ProductCandidate` hypotheses separate from opportunities and Build-domain products.
- One versioned `OpportunityScore` per market opportunity using frozen deterministic formula `v1.0`.
- Typed `OpportunityRisk` records for trademark, brand, policy, dispute, and payment risks.
- Five versioned API resource families and reversible Alembic revision `0004_opportunity_intelligence`.

## Architecture compliance

The new records belong to Intelligence and cannot write Decision venture state, Operations sales state, Build product truth, Finance truth, Governance approvals, or execution state. `MarketOpportunity`, `VentureOpportunity`, and `SalesOpportunity` remain separate. No connector, scraping, external retrieval, LLM, AI agent/scoring, supplier matching, Shopify workflow, or Investment Committee UI was added.

## Validation evidence

- Ruff formatting/lint: passed.
- Mypy strict: passed.
- Pytest: 29 tests passed, including entity, scoring, risk/scope, API, and migration coverage.
- Documentation/link validation passed across 32 Markdown files.
- Docker Compose started PostgreSQL, Redis, API, worker, and web; all defined health checks passed, API/web responses succeeded, and worker readiness was logged.
- Real PostgreSQL upgrade to `0004_opportunity_intelligence`, schema consistency, downgrade to Sprint 003, re-upgrade, and final head verification passed.
- Redis readiness returned `PONG`.
- pip-audit and npm audit found no known third-party dependency vulnerabilities; the unpublished local package is absent from public advisory indexes.
- Next.js lint/build and the Playwright foundation test passed.
- Publication and CI: pending.

## Acceptance mapping

| Acceptance criterion | Status |
|---|---|
| Opportunities, evidence, and candidates modeled | Passed locally |
| Deterministic scoring | Passed locally |
| Risk foundation | Passed locally |
| APIs | Passed locally |
| Migration | Passed on SQLite and real PostgreSQL |
| Automated tests | Passed locally |
| Docker runtime | Passed |
| GitHub Draft PR and CI | Pending |

## Recommendation

**NOT READY FOR SPRINT 005** until publication and remote CI gates pass.
