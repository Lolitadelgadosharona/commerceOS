# Commerce OS Local Development v1.0

Status: implemented Sprint 001 local environment contract

## Baseline

Local development uses Docker Compose to provide reproducible infrastructure and a supported path for running the API in a container. The required services are:

| Service | Purpose | Local persistence/health |
|---|---|---|
| `api` | FastAPI application and OpenAPI endpoint | Source-mounted or image-built development mode; health/readiness endpoint; depends on healthy PostgreSQL/Redis |
| `postgres` | Canonical transactional database and outbox | Named volume; readiness probe; fixed supported major; local data is disposable, never production-derived by default |
| `redis` | Redis Streams/consumer groups for V1 jobs/events plus bounded coordination | Named volume only if needed for stream recovery testing; readiness probe; no canonical business truth |

The Compose root additionally defines `web` and `worker`. The API runs Alembic before startup; the worker checks Redis and remains idle because external delivery is out of scope. Docker was unavailable on the implementation host, so the full Compose runtime still requires verification on a Docker-capable host.

## Developer workflow contract

1. Install supported Docker/Compose, Node.js LTS package tooling, Python tooling, and repository task runner as pinned by Sprint 001.
2. Copy a committed safe `.env.example` to an ignored local environment file; never reuse production secrets or data.
3. Start required services through one documented command.
4. Apply Alembic migrations explicitly; application startup must not auto-create or silently mutate schemas.
5. Run seed/fixture commands that generate synthetic development data only.
6. Run formatting, lint, unit, integration, migration, contract, documentation, and browser checks through documented repository commands.
7. Stop services without deleting volumes by default; destructive local reset is a separate explicit command.

## Environment configuration principles

- Configuration comes from validated environment variables or secret references, with fail-fast startup and no insecure production defaults.
- Commit variable names, descriptions, safe examples, and required/optional status in `.env.example`; never commit values for credentials, tokens, private URLs, or keys.
- Use explicit environment modes (`development`, `test`, `staging`, `production`) and reject unknown modes. Mode does not grant authority.
- Separate database users for migrations and runtime where practical; runtime cannot perform schema administration.
- Bind local services to loopback unless remote access is explicitly required. Do not expose PostgreSQL or Redis in deployed public networks.
- Use S3-compatible local/test storage through a replaceable endpoint when object behavior is needed; it is optional until a Sprint 001 contract requires it.
- Provider integrations default to disabled/fake adapters. No live AI, advertising, payment, messaging, or customer-data provider is required for local foundation work.
- Logs redact secrets and minimize PII. Local test fixtures use synthetic identities.

## Reproducibility and parity

Pin image major/digest policy, dependency lock files, migration heads, and developer commands. CI uses the same PostgreSQL/Redis major versions and the same migration/application commands. Production need not use Docker Compose, but it must honor the same configuration schema, health semantics, migrations, and provider abstractions.

See the [Tech Stack Decision](../architecture/TECH_STACK_DECISION_V1_0.md) and [Quality Gates](./QUALITY_GATES_V1_0.md).
