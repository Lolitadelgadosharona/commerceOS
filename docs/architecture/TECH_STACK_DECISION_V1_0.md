# Commerce OS Tech Stack Decision v1.0

Status: frozen for Sprint 001 implementation

## Decision drivers

The stack must support a small team, explicit domain contracts, transactional business state, append-only events, auditable human authority, asynchronous integrations, provider portability, strong typing at boundaries, migration safety, and a credible path from modular monolith to selective scale-out. Operational simplicity in V1 outranks speculative distribution.

## Frozen stack

| Layer | Selection | Why selected | Principal alternatives rejected for V1 | Scaling path |
|---|---|---|---|---|
| Frontend | Next.js + TypeScript | Mature React application framework; strong type/tool ecosystem; server/client rendering options; accessible dashboard and Playwright support | Vite SPA lacks an integrated server/rendering convention; Remix is capable but adds a second less-familiar convention; native mobile is outside MVP | Cache/read optimization, CDN assets, independently scaled web deployment; add mobile clients against the same API later |
| Backend | Python FastAPI | Typed request/response validation, generated OpenAPI, async I/O, strong Python AI/data ecosystem, lightweight modular-monolith fit | Django adds an opinionated ORM/admin stack that conflicts with the SQLAlchemy choice; Node/NestJS duplicates frontend language but is less aligned with planned Python AI/data work; microservices add premature operational cost | Scale stateless API replicas and workers independently; extract measured domain workloads behind existing contracts |
| Database | PostgreSQL | Strong transactions, constraints, JSON support where justified, indexing, mature backup/PITR, and reliable outbox/ledger foundations | MySQL is viable but offers no project-specific advantage; document databases weaken relational invariants; serverless/proprietary databases risk portability | Read replicas, partitioning, connection pooling, archival, then domain-specific databases only after ownership and workload justify them |
| ORM | SQLAlchemy 2.x | Explicit unit-of-work/session control, mature PostgreSQL support, typed modern API, and separation between domain and persistence | Django ORM couples framework selection; raw SQL everywhere increases repetitive mapping/migration risk; SQLModel hides useful boundary detail for a large domain model | Optimize hot paths with explicit SQL while retaining repository contracts; split persistence adapters if domains are extracted |
| Migration | Alembic | Native SQLAlchemy ecosystem, explicit revision graph and SQL escape hatches, suitable for forward-compatible reviewed migrations | ORM auto-create cannot govern production change; ad hoc SQL lacks revision coordination; proprietary migration services add lock-in | Expand/contract migrations, online operations, backfill jobs, compatibility windows, and deployment gates |
| Queue | Redis, using durable Streams/consumer groups for V1 work delivery | Low-friction local operation, bounded async jobs, rate limiting/caching adjacency, and consumer-group semantics | In-memory background tasks are not durable; Kafka is excessive for V1 operations; RabbitMQ is strong but adds a second operational model before workload evidence | PostgreSQL outbox remains the durable publication source; add dedicated broker/stream platform when throughput, retention, or fan-out exceeds Redis operational limits |
| Object storage | S3-compatible API | Portable object contract, signed access, lifecycle/versioning support, and broad hosted/local implementations | Database blobs harm database operations; local filesystem is not production-safe; provider-specific media APIs cannot be canonical storage | Separate buckets/prefixes, lifecycle tiers, replication/CDN, and provider replacement behind a storage interface |
| Backend testing | Pytest | Flexible fixtures, async support, property/integration ecosystem, and standard Python adoption | `unittest` is lower-level and fixture-poor; bespoke harnesses reduce interoperability | Parallel suites, ephemeral databases, contract/property/security tests, coverage partitioning |
| End-to-end testing | Playwright | Reliable browser automation, tracing, multi-browser support, and first-class TypeScript integration | Cypress is capable but uses a more constrained execution model; Selenium needs more infrastructure; manual-only testing is not an acceptance gate | Sharded browser suites, trace/video artifacts, production-like staging smoke tests |
| CI | GitHub Actions | Repository-native pull-request checks, matrix/services support, security permissions, and common ecosystem | Vendor-specific external CI adds account/credential overhead; local-only checks are unverifiable; self-hosted CI is unnecessary initially | Reusable workflows, protected environments, provenance/signing, optional specialized runners |
| Containers | Docker | Reproducible API/worker builds, standard Compose development, broad deployment portability | Host-only setup drifts; VM images are heavyweight; Kubernetes is an orchestrator rather than a build format and is premature | Hardened multi-stage images, registry scanning/signing, managed container platform; Kubernetes only if operational scale demands it |

## Version policy

Exact supported versions are pinned when Sprint 001 scaffolds manifests and lock files. Use an actively supported Node.js LTS, current supported Next.js major, current stable TypeScript, supported Python release, FastAPI and SQLAlchemy 2.x, supported PostgreSQL major, supported Redis major, and current stable Docker/Compose. Automated dependency updates may propose changes; lockfile and major upgrades require tests and review.

## Architectural consequences

- V1 is a modular monolith: Next.js web application plus FastAPI API and worker processes sharing Python domain/application packages without cross-domain internal imports.
- PostgreSQL is canonical state and transactional outbox truth. Redis is delivery/cache coordination, not the authoritative business ledger or event archive.
- FastAPI/OpenAPI defines HTTP contracts; events have separately versioned schemas.
- SQLAlchemy models are persistence adapters, not domain ownership. Alembic migrations are explicit reviewed artifacts.
- S3-compatible storage owns large object bytes; PostgreSQL stores metadata, ownership, hashes, and references.
- Every provider is behind an interface/adapter; no hosted vendor feature may become the only representation of business state.

## Reconsideration triggers

Revisit a choice only through an architecture decision record with migration/rollback analysis. Valid triggers include measured capacity or reliability limits, security/compliance requirements, end-of-support, unacceptable team operability, or a portability failure. Preference alone is insufficient.

See the [Deployment Topology](./DEPLOYMENT_TOPOLOGY_V1_0.md), [Repository Structure](./REPOSITORY_STRUCTURE_V1_0.md), and [Quality Gates](../engineering/QUALITY_GATES_V1_0.md).
