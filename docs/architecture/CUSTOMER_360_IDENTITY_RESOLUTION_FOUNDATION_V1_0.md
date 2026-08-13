# Customer 360 Identity Resolution Foundation v1.0

Status: implemented foundation; no external connectors or autonomous actions

## Purpose

Customer 360 provides a tenant-scoped, explainable projection of customer identity observations, journey events, conversation activity, risk indicators, and advisory value assessments. It is a view over domain-owned records and is never a source of truth.

## Ownership

| Capability | Owner | Authority |
|---|---|---|
| Customer and conversation records | Operations | Operational source of truth |
| Customer identity links | Operations | Records supplied identity observations; no external verification |
| Journey events and Customer 360 projection | Intelligence | Observation and projection only |
| Customer value assessment | Decision | Advisory deterministic assessment only |
| Revenue and margin truth | Finance | Sole monetary source of truth |
| Access and approval policy | Governance | Permission and authority controls |

Intelligence may read domain records through stable table contracts to calculate a projection. It cannot update Customer, Conversation, Finance, or Decision source records. Rebuilding a projection may only insert or update `Customer360Profile`.

## Data contracts

### CustomerIdentityLink

A tenant-scoped link between an Operations-owned Customer and a supplied identity reference. Supported identity types are `email`, `social`, `website`, `chat`, and `other`. Confidence is bounded from zero to one. No connector validates, enriches, or contacts the identity.

### CustomerJourneyEvent

An immutable-style observation referencing a customer and, optionally, a matching tenant-scoped identity link. Supported initial event types cover content views, clicks, conversations, purchase references, support requests, and refund references. Purchase and refund events are references—not orders, revenue, refunds, or Finance entries.

### Customer360Profile

A materialized projection containing counts, summaries, and last activity. The profile has no create or update API. A scoped read can rebuild it from current records. It does not resolve conflicts, merge customers, or mutate source records.

### CustomerValueAssessment

A Decision-owned advisory assessment using supplied indicators. Formula v1.0 is:

`20% revenue + 20% margin + 25% repeat probability + 20% strategic potential - 15% risk`

The result is bounded to 0–100. Revenue and margin inputs are indicators, not monetary facts; Finance remains authoritative.

## API boundary

- `/api/v1/customer-identity-links`: create and list scoped identity observations.
- `/api/v1/customer-journey-events`: create and list scoped observations.
- `/api/v1/customer-360`: list stored projections.
- `/api/v1/customer-360/{customer_id}`: read and refresh one projection.
- `/api/v1/customer-value-assessments`: create and list advisory assessments.

All contracts require organization scope. Cross-tenant customer and identity references are rejected.

## Explicit exclusions

No Shopify, payments, order synchronization, messaging connector, external identity validation, customer merge, outbound communication, autonomous action, or AI-agent execution is present.
