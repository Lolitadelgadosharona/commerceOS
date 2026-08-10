# Sprint 012 — AI Sales and Support Decision Foundation Completion

Status: implementation and runtime validation complete; remote publication pending

## Delivered scope

- Decision-owned sales intelligence profiles grounded in matching customer, conversation, intent, and optional product evidence.
- Controlled sales recommendation lifecycle with confidence and rationale.
- Supplied support-case intelligence and evidence-linked customer-risk signals.
- Governance-owned AI action policies with safe advisory defaults and mandatory approval boundaries for non-advisory actions.
- Five `/api/v1` resource families and reversible Alembic revision `0012_ai_sales_support`.

## Architecture compliance

Decision owns advice; Operations owns conversation/support execution; Governance owns action policy, permission, and approval; Finance owns financial truth; Build owns Product Truth. AI is recommendation/provenance only. No LLM, agent, automated classification/reply, messaging, refund, discount, payment, or external integration was added.

## Validation evidence

- Ruff formatting/lint: passed.
- Strict mypy: passed.
- Pytest: 49 tests passed locally, including aggregation evidence, lifecycle, support classification, risk, authority policy, APIs, tenant isolation, boundaries, and migrations.
- Documentation structure and relative links passed across 48 Markdown files.
- Docker Compose started PostgreSQL, Redis, API, worker, and web; all defined health checks passed, API/web smoke checks succeeded, and worker readiness was logged.
- Real PostgreSQL upgraded to `0012_ai_sales_support`, reported no schema drift, downgraded to Sprint 011, re-upgraded, and finished at the Sprint 012 head.
- Next.js type checking/build and one Playwright foundation test passed.
- pip-audit and npm audit found no known third-party dependency vulnerabilities; the unpublished editable local package is absent from public advisory indexes.
- The Sprint 002 authentication limitation remains enforced: the API must not be publicly deployed.

## Recommendation

**READY FOR SPRINT 013, subject to remote CI.** Local implementation, runtime, migration, documentation, and security gates pass.
