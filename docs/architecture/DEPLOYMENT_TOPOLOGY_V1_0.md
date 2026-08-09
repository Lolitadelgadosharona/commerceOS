# Commerce OS Deployment Topology v1.0

Status: logical vendor-neutral topology aligned to the frozen [Tech Stack Decision](./TECH_STACK_DECISION_V1_0.md)

## V1 topology

```mermaid
flowchart LR
  U["Owner/operator browser"] --> F["Frontend"]
  F --> B["Backend/API"]
  B --> DB["Transactional database"]
  B --> S["Object storage"]
  B --> Q["Durable queue/event delivery"]
  Q --> W["Worker processes"]
  W --> DB
  W --> S
  B --> IA["Integration adapter layer"]
  W --> IA
  IA --> EXT["Commerce, payment, channel, messaging providers"]
  B --> AI["AI provider abstraction"]
  W --> AI
  AI --> MODELS["Replaceable model providers"]
  SM["Secret manager"] --> B
  SM --> W
  B --> O["Logs, metrics, traces, audit"]
  W --> O
```

## Components and boundaries

| Component | Responsibility | Boundary/control |
|---|---|---|
| Frontend | Next.js + TypeScript authenticated owner/operator interface and read/command presentation | No secrets, direct database access, authority decisions, or trusted validation |
| Backend/API | Python FastAPI authentication boundary, authorization/policy checks, domain commands/queries, approval enforcement | Stateless where practical; business truth persists only through owning repositories |
| Transactional database | PostgreSQL canonical aggregates, approval/audit references, outbox, registry/configuration through SQLAlchemy/Alembic | Transactional integrity, encryption, backup/PITR, least privilege |
| Object storage | S3-compatible large creative assets, documents, sensitive content references, exports | Organization-prefixed access, encryption, signed short-lived access, lifecycle/retention controls |
| Queue/event system | Redis Streams/consumer groups for V1 asynchronous delivery; PostgreSQL outbox is durable publication truth | At-least-once assumption, idempotent consumers, bounded retries/dead-letter handling; Redis is not canonical business state |
| Worker processes | Python background integrations, projections, backfills, model execution, event consumers | Same policy/identity controls as API; bounded retries and cost/time limits |
| AI provider abstraction | Normalized capability requests/results, routing, provenance, safety/cost/data policy | Providers never receive authority credentials or own canonical state; disable/fallback/version pinning |
| Integration layer | Adapters for commerce, payments, messaging, ads, suppliers, and channels | Normalizes IDs/receipts, verifies callbacks, rate limits, isolates credentials, supports replacement |
| Secret manager | Runtime delivery and rotation of credentials/keys | No secret values in code, client, logs, events, prompts, or database configuration records |
| Observability/audit | Operational logs/metrics/traces plus protected business audit | PII minimization, correlation IDs, tamper-evident audit, retention/access controls |

## Deployment principles

- Begin with the smallest operational unit consistent with boundaries: one frontend, one backend deployment, one worker deployment, one transactional database, object storage, and durable event delivery.
- Logical domains need not be separately deployed services in V1. Enforce module ownership in code/contracts first; split deployments only for measured scaling, security, or reliability needs.
- Separate local/development, test/staging, and production identities, data, credentials, and provider accounts. Production access is audited and least privilege.
- Use reproducible build artifacts, declarative configuration, forward-compatible migrations, health checks, controlled rollout/rollback, backups, and recovery tests.
- Technology changes require architecture decision records based on transactional guarantees, operability, portability, cost, recovery, and team capability—not provider-specific convenience.

## Failure and recovery assumptions

Provider calls fail independently; queues deliver more than once; callbacks may be delayed, duplicated, forged, or reordered; model output is untrusted; storage can be temporarily unavailable. Commands use idempotency keys, events use correlation/causation, integrations reconcile receipts, and consequential partial failure enters visible exception/handoff state rather than silently retrying financial action.
