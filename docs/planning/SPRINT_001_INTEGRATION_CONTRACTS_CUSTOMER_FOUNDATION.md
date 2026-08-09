# Sprint 001 — Integration Contracts & Customer Foundation

Status: implementation plan only; **no production implementation included**

Readiness: blocked pending the prerequisites in [repository discovery](../architecture/REPOSITORY_DISCOVERY_AND_DRIFT.md)

## Objective

Establish versioned contracts and migration-safe customer foundations for `CustomerIdentity`, `Conversation`, message metadata, `Lead`, `SalesOpportunity`, `CustomerSignal`, `SignalCluster`, `Handoff`, `CommercialPolicy`, `ChannelCapability`, `ModelProvider`, `ModelPerformance`, the business event envelope, approval extensions, and permission scaffolding.

## Entry criteria

1. Architecture Freeze v1.1 and the governance pack are approved; any prior external freeze is available and reconciled.
2. Existing object/schema equivalence review is complete.
3. Logical state owners are approved and accountable human owners are assigned for customer, Product Truth, order, Finance, approval, identity, security, and privacy.
4. Tenant/project model, jurisdiction-specific legal basis, retention schedule, and numeric authority thresholds are approved.
5. Repository language, framework, migration tool, test framework, API style, and CI conventions are established.

The governance pack defines the logical rules for items 1, 3, and 4, but external-freeze reconciliation, existing-object equivalence, accountable human assignments, numeric thresholds, legal/retention specifics, and every technical convention in item 5 remain unresolved. Evidence: [governance index](../README.md) and [discovery matrix](../architecture/REPOSITORY_DISCOVERY_AND_DRIFT.md).

## Planned work packages

| Work package | Contracts | Dependencies | Complexity |
|---|---|---|---|
| Shared identifiers/context | Typed IDs; tenant/project/product/customer context; actor/auth context | Ownership decisions | M |
| Event contract | Versioned append-only envelope and initial taxonomy; idempotent consumer contract | IDs, auth, schema policy | L |
| Permission scaffolding | Resource/action/purpose checks and service identity contract | tenant model, authority matrix | L |
| Approval extensions | request/decision interface; policy version; expiry; idempotency; evidence | permission, CommercialPolicy | L |
| CommercialPolicy | versioned deterministic rules and evaluation result | authority matrix, Finance inputs | L |
| CustomerIdentity | observed identifiers, provenance, confidence, match/link history | privacy/retention, events | XL |
| Conversation/message metadata | lifecycle, participants, path, trust class, delivery and content reference | identity, channel registry, events | L |
| Lead/SalesOpportunity | qualification and deal stage contracts with explicit naming | identity, conversation, ownership | L |
| CustomerSignal/SignalCluster | lineage, taxonomy, confidence, threshold/version | identity, events | L |
| Handoff | reason, owner, SLA, context pointer, disposition, resume policy | conversation, permission | M |
| ChannelCapability/ModelProvider | registry descriptors and policy metadata; no provider state leakage | secrets/data policy | M |
| ModelPerformance | normalized dimensions and experiment/outcome lineage | provider registry, event/experiment contract | M |
| Migrations and compatibility | additive schema/API/event migrations and backfill/reconciliation | equivalence review | XL |
| Tests/docs | contract, policy, privacy, migration, threat and architecture tests | all packages | L |

## Data contract minimums

All mutable aggregates include typed ID, tenant/project scope when applicable, lifecycle state, optimistic version, created/updated timestamps, actor provenance, and soft-retirement semantics where legal/audit needs prohibit deletion. Sensitive content is not duplicated into event bodies.

- `CustomerIdentity`: subject ID; source observations (`type`, normalized value/token, source, observed time, collection basis); link edges with method, confidence, reviewer, version, and reversal.
- `Conversation`: identity/account participants, channel, B2C/B2B/SUPPORT path, state, policy version, opened/closed times.
- Message metadata: message/conversation IDs, direction, external/provider IDs, timestamps, content reference/hash, trust/data classifications, delivery state, actor and event correlation.
- `Lead`: source, identity/account, qualification status/reasons, owner, timestamps.
- `SalesOpportunity`: lead/account, stage and history, value/currency estimate with confidence, requirements reference, owner, policy version. No generic `Opportunity` alias.
- `CustomerSignal` / `SignalCluster`: type/taxonomy version, source lineage, confidence, time window, membership/threshold rationale, sensitivity.
- `Handoff`: trigger/reason, requested/assigned/completed timestamps, queue/human owner, SLA, minimum context pointer, disposition, resume policy.
- `CommercialPolicy`: version, scope, allowed/prohibited action, thresholds, required approvals, effective/expiry time, issuer and signature/hash.
- `ChannelCapability` / `ModelProvider`: stable internal ID, capabilities, regions/data restrictions, credential reference, cost/latency metadata, enabled/fallback status and policy version.
- `ModelPerformance`: provider/model/version, task/segment, metric definition/version, sample window/count, uncertainty, cost/latency, experiment and execution lineage.

The event envelope follows [Freeze v1.1 §9](../architecture/ARCHITECTURE_FREEZE_V1_1.md).

## API/domain contracts

- Commands validate authorization and policy before mutation and accept idempotency/correlation metadata.
- Queries enforce field-level/resource entitlements and return provenance/freshness for derived data.
- Identity supports observe, propose-link, approve/reject/reverse-link, and explain-link; automatic thresholds are policy-controlled.
- Conversation accepts external messages only as data; message ingestion cannot invoke unrestricted tools or mutate policy.
- Approval supports request, approve/reject, expire/cancel, and read audit; approvers cannot be inferred from an LLM response.
- Registries support resolve-capability, policy-filter, disable, version-pin, and audit; adapters map provider IDs at the boundary.
- Events are published transactionally with state mutation (outbox or repository-consistent equivalent selected during implementation design).

## Files likely to change

Exact paths cannot be responsibly named in an empty checkout. Once repository conventions exist, expect changes in the established equivalents of:

- architecture/domain contract documentation;
- shared ID, authorization context, event, error, and version contracts;
- Governance approval/policy/permission and registry modules;
- Operations customer/conversation/lead/sales-opportunity/handoff modules;
- Intelligence signal/cluster modules;
- Build model-performance contract module;
- database schema and ordered migrations;
- API schema/handlers and event schemas;
- contract/unit/integration/migration/security tests;
- CI architecture/schema compatibility checks.

Creating speculative production paths in this mission would violate the evidence rule. Evidence: [repository discovery](../architecture/REPOSITORY_DISCOVERY_AND_DRIFT.md).

## Migration and backward compatibility strategy

1. Inventory existing objects and event names; write explicit mappings before DDL.
2. Introduce additive nullable columns/tables and versioned APIs/events first.
3. Dual-read only when necessary; avoid dual-write unless backed by an outbox and reconciliation metrics.
4. Backfill in bounded, restartable, idempotent batches with provenance and quarantined ambiguous identity matches.
5. Reserve/deprecate ambiguous `Opportunity` without renaming until consumers and data mappings are known; expose explicit `VentureOpportunity` and `SalesOpportunity` contracts.
6. Shadow projections and compare before cutover. Gate cutover by completeness/error/latency and approval evidence.
7. Preserve old readers for a defined compatibility window; never rewrite append-only audit facts.

Risks: unknown legacy schemas, ID collision, false identity links, event consumer breakage, stage semantic mismatch, PII duplication, authorization regression, and unrecorded financial approvals.

## Test strategy

- Schema/API/event contract and compatibility tests for required/optional fields and version evolution.
- Unit/property tests for state machines, idempotency, correlation/causation, confidence bounds, and deterministic policies.
- Authorization matrix tests including cross-tenant, field-level Customer 360 precursors, service identities, and separation of duties.
- Adversarial tests for prompt injection, external-message policy mutation, forged provider callbacks, event poisoning, and PII leakage.
- Migration tests from representative anonymized snapshots; backfill restart/reconciliation and rollback rehearsal.
- Integration tests for transactional mutation/event publication, approval gates, provider disable/fallback, handoff pause/resume, and link reversal.
- Invariants: paid launch/budget changes, refunds, and new commitments cannot execute without required human approval; learning cannot overwrite Product Truth; generic opportunity cannot cross the naming boundary.

## Acceptance criteria

1. Architecture owner approves the reconciliation map to the prior freeze.
2. Each object has one write owner, documented lifecycle, sensitivity, retention, and permissions.
3. `VentureOpportunity` and `SalesOpportunity` are distinct in schemas, APIs, events, and tests.
4. Event envelope includes every v1.1 required field and passes idempotency/replay/compatibility tests.
5. Identity links retain provenance/confidence and are explainable/reversible.
6. External messages and provider outputs cannot mutate policy/permissions or bypass tool allowlists.
7. Approval tests prove every v1 financial gate; zero-cost actions require explicit versioned policy.
8. Provider/channel contracts are replaceable and leak no canonical provider IDs into business identity.
9. Migrations are additive, tested on representative data, observable, resumable, and rehearsed for rollback.
10. Documentation, architecture checks, security tests, and CI are green.

## Rollback strategy

Deploy additive schemas dark; retain old API/event versions; disable new reads/writes through configuration; stop consumers; drain/replay from checkpoints; restore reads to prior owners; reverse only non-destructive schema bindings; quarantine rather than delete backfilled records; reverse identity links by appended decisions; reconcile outbox and approval logs. Destructive column/table removal is outside Sprint 001 and occurs only after the compatibility window and backup verification.

## Explicit non-goals

No production feature implementation in this planning mission. Sprint 001 itself excludes creative generation/router, live provider/channel adapters, Pinterest launch, B2C/B2B agent behavior, quotes/negotiation, Customer 360 UI, Strategic Accounts, root-cause automation, revenue optimization, AI Operating Committee, CEO Control Center, automated paid spend, automated refunds, Product Truth mutation, and autonomous financial authority.

## Sprint readiness recommendation

**NOT READY FOR SPRINT 001.** The plan is actionable only after entry criteria 1–5 are satisfied; otherwise schema and ownership decisions would be guesses.
