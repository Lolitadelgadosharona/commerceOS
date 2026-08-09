# Commerce OS MVP Boundary v1.0

Status: Phase 1 scope-control contract

## Phase 1 must include

- the eight-domain architecture boundary and canonical ownership contracts;
- typed identifiers and explicit `VentureOpportunity` versus `SalesOpportunity` separation;
- append-only business event envelope, schema/version policy, idempotency, correlation, and audit;
- authentication context, least-privilege permission scaffolding, and human Approval Service contract;
- deterministic `CommercialPolicy` and the v1 Finance Authority Model;
- `CustomerIdentity` observations with provenance/confidence and safe reversible resolution;
- `Conversation`, message metadata, `Lead`, `SalesOpportunity`, `CustomerSignal`, `SignalCluster`, and `Handoff` foundations;
- `ChannelCapability`, `ModelProvider`, and `ModelPerformance` registry/contracts without live provider lock-in;
- migrations, compatibility/rollback design, contract/security/migration tests, and architecture documentation;
- a narrow read-only owner operating summary using verified test or authorized source data, only after foundations pass acceptance gates.

## Phase 1 explicitly excludes

- production creative generation/router, live short-video/image generation, and autonomous creative approval;
- live Pinterest or other paid-channel launch and automatic advertising budget changes;
- autonomous AI Sales/Support behavior, Negotiation Copilot commitments, automated refunds, supplier payments, custom commitments, or pricing exceptions;
- production B2C/B2B conversation execution beyond foundation contracts and controlled test harnesses;
- quote automation, Strategic Accounts automation, full Customer 360, root-cause automation, revenue optimization, AI Operating Committee automation, and CEO command center;
- self-modifying policy/prompts/permissions, learning writes to Product Truth, generic `Opportunity`, or provider-owned canonical state;
- full ERP, CRM, accounting, payment processing, data warehouse, every channel/provider, native mobile applications, or multi-region scale unless separately approved;
- destructive legacy migrations or removal of compatibility paths.

## Scope-control rule

An item enters Phase 1 only if it is required for a listed acceptance criterion or removes a documented safety/compatibility blocker. Every proposed addition must include owner, user outcome, dependency, data/security/financial impact, complexity, tests, rollback, and the Phase 1 item it enables. The accountable product owner, architecture owner, and Governance owner approve boundary changes; Finance and Security/Privacy approval is additionally required when their controls are affected.

New provider/channel integrations, autonomous actions, UI expansion, analytics enrichment, or “while we are here” refactors default to the backlog. Schedule pressure does not weaken authority, security, privacy, audit, migration, or rollback requirements. If scope and quality conflict, reduce scope.

## Phase 1 exit conditions

All included contracts have one owner and passing acceptance tests; required approval gates cannot be bypassed; identity links are explainable/reversible; migration and rollback are rehearsed; provider replacement is contract-tested; sensitive-data controls are verified; documentation links and architecture checks pass; and no excluded production behavior is enabled.

See the [PRD](./COMMERCE_OS_PRD_V1_0.md), [Sprint 001 Plan](../planning/SPRINT_001_INTEGRATION_CONTRACTS_CUSTOMER_FOUNDATION.md), and [Architecture Freeze](../architecture/ARCHITECTURE_FREEZE_V1_1.md).
