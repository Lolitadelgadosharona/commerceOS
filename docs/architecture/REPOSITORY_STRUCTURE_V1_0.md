# Commerce OS Repository Structure v1.0

Status: frozen target layout; directories are created during Sprint 001 scaffolding, not by this planning mission

## Target layout

```text
apps/
  web/                    # Next.js + TypeScript owner interface
  api/                    # FastAPI composition root and HTTP adapters
  worker/                 # Async job/event consumer composition root
packages/
  backend/
    commerce_os/          # Python modular-monolith source package
      shared/             # Narrow technical primitives; no business ownership
      intelligence/
      decision/
      build/
      growth/
      operations/
      finance/
      learning/
      governance/
  contracts/              # Versioned API/event schemas and generated-client inputs
  frontend/               # Reusable UI/design-system and typed client packages
infra/
  docker/                 # Production image definitions and entrypoints
  compose/                # Local/test service composition
  deployment/             # Vendor-neutral deployment manifests added when target is chosen
docs/
  architecture/
  engineering/
  governance/
  planning/
  product/
tests/
  contract/
  integration/
  architecture/
  e2e/
```

Root manifests, lock files, `.github/workflows`, configuration examples, license/security policy, and developer commands are added by the repository-foundation work in Sprint 001.

## Responsibilities

| Area | Responsibility | Must not contain |
|---|---|---|
| `apps/web` | Next.js routes, presentation, authenticated interaction, server/client composition | Business authority, direct database/provider access, canonical domain logic |
| `apps/api` | FastAPI startup, dependency wiring, middleware, HTTP routes, OpenAPI, health/readiness | Domain state ownership or cross-domain SQL shortcuts |
| `apps/worker` | Worker startup, queue consumers, scheduled/background composition | Unbounded retries, hidden approval bypass, canonical logic duplicated from packages |
| `packages/backend` | Domain, application, port, and adapter modules for the modular monolith | Framework composition roots, frontend code, undocumented cross-domain imports |
| `packages/contracts` | Versioned OpenAPI/event schemas, fixtures, generated-client inputs | Secrets, provider-specific canonical models, unversioned breaking changes |
| `packages/frontend` | Shared accessible UI, tokens, typed client support | Business decisions or server credentials |
| `infra` | Build/runtime/deployment definitions and environment wiring | Business rules, committed secrets, vendor coupling without an abstraction decision |
| `docs` | Product, architecture, governance, engineering, planning, ADRs/runbooks | Generated runtime state or credentials |
| `tests` | Cross-application contract, integration, architecture, and browser suites | Production-only configuration or reliance on shared mutable external environments |

## Backend module shape

Each domain package uses the same conceptual layers only where useful:

```text
domain/          # aggregates, value objects, policies, domain events
application/     # commands, queries, workflows, ports
infrastructure/  # SQLAlchemy repositories, external adapters
api/             # transport-neutral request/response mapping or router contribution
tests/           # domain-local unit tests may live beside the package
```

Composition roots in `apps/api` and `apps/worker` connect modules. Cross-domain access uses public application ports, typed IDs/contracts, or events; modules never import another domain’s `infrastructure` or ORM models.

## Dependency direction

Domain code depends on standard-library/narrow approved primitives, not FastAPI, SQLAlchemy, Redis, S3, or provider SDKs. Application code depends inward on domain and outward-facing ports. Infrastructure implements ports. Apps depend on application/public interfaces and infrastructure wiring. Tests may use public seams but architecture tests enforce production dependency rules.
