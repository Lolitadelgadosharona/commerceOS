# GrowthOS Conversation Intelligence Foundation v1.0

Status: Frozen for Sprint 051

## Purpose

GrowthOS Conversation Intelligence converts founder-supplied customer replies into governed,
reusable sales intelligence. Its closed loop is:

`Conversation → Analysis → Human Review → Learning Observation → Future Recommendation`

The objective is learning quality, not autonomous selling. No component introduced here sends
a message, contacts a customer, negotiates, approves a discount, promises delivery, creates a
contract, or changes source truth.

## Ownership

Growth owns the prospect conversation analysis, objection records, message-performance
observations, and GrowthOS sales dashboard. Learning owns `LearningObservation` and all later
hypotheses, conclusions, and improvement recommendations. AI Runtime owns provider-neutral
execution provenance. Governance owns identity, permission, audit, and authority boundaries.
Operations, Customer, Product Truth, and Finance retain their existing sources of truth.

GrowthOS records reference human-supplied interaction evidence. They do not become the
customer conversation master or financial outcome truth.

## Governed conversation analysis

The existing `SalesConversationAnalysis` is extended instead of duplicated. A governed AI
request may produce structured intent, sentiment, buying signal, objection category, urgency,
recommended next action, and a suggested reply draft. Only `analysis`, `classification`,
`recommendation`, and `draft` output classes are accepted.

Analyses move through `draft → reviewed → accepted` or terminate as `rejected`. Review and
acceptance are explicit human actions. A draft cannot become a Learning input directly.
Suggested replies remain text for human review and have no transport or execution adapter.

## Objection intelligence

`GrowthObjectionRecord` copies the cited original customer message and suggested response from
a human-reviewed analysis. Categories are `price`, `timing`, `trust`, `existing_supplier`,
`no_need`, `wrong_contact`, and `other`. Outcomes are supplied observations: `pending`,
`resolved`, `unresolved`, `lost`, or `converted`.

An objection record cannot rewrite the source analysis. Its customer segment is analytical
metadata, not Customer master truth.

## Closed-loop learning integration

An accepted analysis can create `GrowthSalesLearningSignal`. The service simultaneously uses
Sprint 042 `ClosedLoopLearningService` to append a `LearningObservation` whose source is the
exact conversation analysis. The Growth signal links that observation and retains the insight,
future advisory recommendation, confidence, and optional objection reference.

This integration deliberately stops at observation and recommendation. It does not create a
supported hypothesis, conclusion, workflow action, outreach draft, or source-truth mutation.
Those later lifecycle steps keep the existing Sprint 042 human review rules.

## Message performance and dashboard

`GrowthMessagePerformanceObservation` is append-only. It records a founder-supplied outcome
for a previously human-approved outreach record, with optional Revenue Experiment assignment,
segment, strategy, timestamp, confidence, and provenance metadata. The service has no sender.

The read-only Sales Knowledge Dashboard aggregates:

- most common objection categories;
- message strategies with positive or converted observations;
- supplied reply rate observations;
- positive buying signals;
- objection categories associated with lost outcomes; and
- segment-level reply and positive outcomes.

Dashboard values are operational intelligence, not causal claims or Finance truth. Sparse or
missing observations remain visible rather than inferred.

## AI routing and security

The existing tenant-scoped `AIModelPolicy` supports economy tasks for conversation
classification, sentiment, and tagging, and higher-reasoning tasks for complex customer
reasoning, reply drafting, and negotiation preparation. Negotiation preparation means internal
analysis only; the system cannot negotiate. Providers are never hardcoded.

All APIs inherit production authentication, organization scope validation, RBAC, domain
authorization, and audit logging. Tenant boundaries apply to analyses, objections, learning
signals, observations, performance records, and dashboard queries. There are no public
GrowthOS endpoints.

## Explicit exclusions

Sprint 051 adds no email or social sender, autonomous sales agent, customer contact, automatic
reply, negotiation, discount, contract, promise, checkout, payment, CRM, customer account,
external connector, or parallel AI/Learning runtime.
