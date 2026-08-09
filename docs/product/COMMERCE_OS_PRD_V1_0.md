# Commerce OS PRD v1.0

Status: product requirements baseline; implementation-neutral

## Product goals

1. Give a commerce owner one trustworthy operating view across opportunities, products, customers, orders, operations, finance, experiments, and learning.
2. Convert evidence into explainable recommendations and governed execution without creating a parallel source of truth.
3. Make authority, economics, exceptions, and outcomes visible end to end.
4. Support B2C and B2B conversion paths with shared foundations but distinct deal semantics.
5. Keep model, messaging, channel, and advertising providers replaceable.

## Target user

The primary user is an accountable founder-owner or commerce CEO operating a small-to-mid-sized portfolio with limited specialist capacity. Secondary users are explicitly delegated finance, growth, operations, support, sales, and governance operators. Providers, agents, and integrations are execution participants—not owners.

## Owner workflow

1. Establish Product Truth, goals, policy, authority, budgets, and data access.
2. Review an evidence-backed daily/weekly operating brief and exceptions.
3. Inspect recommendations with economics, confidence, dependencies, and alternatives.
4. Approve, reject, edit, delegate, or schedule allowed actions.
5. Monitor execution, customer impact, operational health, cash, and exceptions.
6. Review experiments and learning; promote changes only through versioned policy/product governance.

## CEO Dashboard vision

The CEO Dashboard is a permissioned control center over existing domain owners, never a new database. It should present:

- business health: revenue, contribution, cash, expenses, commitments, forecast confidence;
- portfolio/product truth and `VentureOpportunity` status;
- customer, order, support, B2B `SalesOpportunity`, and strategic-account health;
- channel/creative performance with attribution uncertainty;
- approvals awaiting decision, policy exceptions, risks, incidents, and handoffs;
- experiments, learning, root causes, and corrective actions;
- drill-down lineage from metric → evidence → recommendation → approval → action → outcome.

Command controls appear only when the viewer has authority and always show policy/approval consequences.

## Core business workflows

- venture discovery → evidence → `VentureOpportunity` decision → Product Truth;
- product/supplier readiness → build assets → launch readiness;
- creative hypothesis → generation/QA → experiment → channel recommendation;
- B2C conversation → identity → recommendation → governed order/support/handoff;
- B2B lead → `SalesOpportunity` → requirement profile → quote/negotiation → approval;
- order → fulfillment → transaction/revenue/expense reconciliation → support/refund/dispute;
- signal → cluster → root-cause case → corrective action → approval → learning;
- operating review → exceptions/approvals → delegated execution → outcome review.

## MVP scope

The MVP establishes the governed system foundation and a narrow owner workflow: canonical contracts, ownership, identity provenance, append-only events, permissions, approvals, financial gates, provider/channel registries, auditable customer/conversation foundations, and a read-only operating summary using verified data. Detailed Phase 1 scope is frozen in the [MVP Boundary](./MVP_BOUNDARY_V1_0.md).

## Non-goals

- autonomous CEO/CFO, autonomous financial authority, or self-modifying policy;
- replacing accounting, payment, commerce, ad, messaging, or provider systems of record;
- every channel/provider, full ERP/CRM, general-purpose workflow automation, or custom data warehouse;
- causal certainty from attribution, guaranteed profit, or fully autonomous product/creative strategy;
- a single generic opportunity type or Customer 360 master database.

## Acceptance principles

- Every material state has one owner and source of truth.
- Facts, estimates, recommendations, approvals, actions, and learning remain distinguishable.
- Every consequential action is authenticated, authorized, policy-checked, idempotent where applicable, and auditable.
- Required human approvals are proven before execution.
- AI and external providers cannot override policy or own canonical business state.
- Sensitive data is minimized and purpose-bound; identity links are explainable and reversible.
- Product Truth and financial truth cannot be overwritten by learning.
- Provider replacement and rollback are demonstrated, not merely asserted.
- B2C and B2B paths share foundations without conflating `VentureOpportunity` and `SalesOpportunity`.
- Scope additions pass the MVP change-control rule.

This PRD is constrained by the [Constitution](../governance/AI_COMMERCE_OS_CONSTITUTION_V1_0.md) and [Architecture Freeze](../architecture/ARCHITECTURE_FREEZE_V1_1.md).
