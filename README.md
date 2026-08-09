# Commerce OS

Commerce OS is a governed modular-monolith foundation for evidence-backed commerce operations. Sprint 001 implements repository, customer/domain-contract, API, event/outbox, migration, testing, and CI foundations only. It does not enable AI agents, external integrations, automated financial actions, or customer-facing business workflows.

> **Security status:** The Sprint 001 CRUD API does not yet enforce production authentication or authorization. Do not expose or deploy it publicly. Production credentials must be supplied through an approved external secret manager/environment mechanism; never place secrets in `.env.example`, source, client configuration, logs, or events.

## Architecture

Start with the [architecture and governance index](./docs/README.md), especially:

- [Architecture Freeze v1.1](./docs/architecture/ARCHITECTURE_FREEZE_V1_1.md)
- [Tech Stack Decision v1.0](./docs/architecture/TECH_STACK_DECISION_V1_0.md)
- [Repository Structure v1.0](./docs/architecture/REPOSITORY_STRUCTURE_V1_0.md)
- [Module Boundary v1.0](./docs/architecture/MODULE_BOUNDARY_V1_0.md)
- [Sprint 001 Plan](./docs/planning/SPRINT_001_INTEGRATION_CONTRACTS_CUSTOMER_FOUNDATION.md)

## Local startup

Prerequisite: a current Docker installation with Docker Compose.

```bash
cp .env.example .env
docker compose up --build
```

Services:

- Web shell: <http://localhost:3000>
- API/OpenAPI: <http://localhost:8000/docs>
- Health: <http://localhost:8000/api/v1/health>
- PostgreSQL and Redis are internal Compose services without host ports.

The API container runs `alembic upgrade head` before startup. The worker verifies Redis readiness and then remains idle; external event delivery is intentionally not implemented.

Stop without deleting local data:

```bash
docker compose down
```

Delete only the local Compose volumes:

```bash
docker compose down --volumes
```

## Host development

Use Python 3.11–3.13 and Node.js 22.

```bash
python -m venv .venv
.venv/bin/pip install -e '.[dev]'
cd apps/web && npm ci && cd ../..
```

With PostgreSQL and Redis available and environment variables configured:

```bash
.venv/bin/alembic upgrade head
.venv/bin/uvicorn apps.api.main:app --reload
.venv/bin/python -m apps.worker.main
npm --prefix apps/web run dev
```

## Quality checks

```bash
.venv/bin/ruff format --check .
.venv/bin/ruff check .
.venv/bin/mypy packages/backend apps
.venv/bin/pytest
ruby scripts/validate_docs.rb
npm --prefix apps/web run lint
npm --prefix apps/web run build
```

Docker Compose validation requires Docker and is reported separately when the Docker CLI/daemon is unavailable.
