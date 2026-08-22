# Revenue Experiment Execution Layer v1.0

Status: frozen for Sprint 059 Product Review

## Purpose

The Revenue Experiment Execution Layer turns existing GrowthOS intelligence into a governed daily
operating workflow:

Industry selection → Prospect discovery → Evidence analysis → Growth opportunity → Growth Gift →
Outreach preparation → Sales Copilot → Conversion learning.

Beauty is the initial operating profile. All contracts remain reusable across Pet, Home,
Industrial, B2B, and future verticals.

## Daily opportunity queue

`DailyGrowthOpportunity` composes existing records rather than duplicating them. Every queue item
references one tenant-scoped Industry Profile, Prospect, Prospect Evidence set, Industry Pattern,
and Growth Service Recommendation. A Growth Gift may be linked when available.

Opportunity score is optional. Missing inputs remain null; the queue never fabricates a score. New
items enter `review` and do not initiate external actions.

## Growth Gift pipeline

The Growth Gift lifecycle supports:

`draft → review → approved → sent → customer_response → converted`

Existing `ready_for_delivery` and `delivered` states remain compatible. Approval is mandatory
before `sent`. The state records a human action performed outside the system; it does not send an
asset. Gift type, evidence, before/after references, customer-specific rationale, and observed
response remain auditable.

## Outreach and Sales Copilot

Outreach drafts may cite an Industry Profile and explicit industry context. Existing checks reject
AI self-reference, generic agency language, fake guarantees, and exaggerated ROI claims. Drafts
remain human-review artifacts and never send themselves.

Sales Conversation Analysis may include the same Industry Profile and context so objections can be
interpreted without replacing customer evidence. Recommendations and reply drafts remain advisory.

## Revenue dashboard

The read-only projection reports prospect, Gift, outreach, response, conversation, and customer
counts from GrowthOS truth. Revenue is read from Finance-owned Revenue Observations. It never writes
Finance records.

MRR and LTV remain null when Finance does not provide an authoritative recurring-revenue or unit
economics value. Multiple currencies are not combined; currency and monetary aggregates remain
unset rather than presenting a misleading total.

## Model routing

Existing GrowthOS model policy now records task type, provider registry alias, preferred and
fallback model aliases, cost policy, optional cost limit, and quality requirement. No provider is
hardcoded and this sprint introduces no direct provider execution. A capped policy requires an
explicit limit.

## Authority and security

- Authentication, RBAC, tenant isolation, evidence ownership, and audit logging remain mandatory.
- Human approval is required before external communication is recorded.
- AI may analyze, classify, recommend, and draft.
- AI cannot send, sell, negotiate, discount, sign, collect payment, promise outcomes, or make a
  commitment.
- GrowthOS remains an internal revenue operating application, not SaaS packaging.
