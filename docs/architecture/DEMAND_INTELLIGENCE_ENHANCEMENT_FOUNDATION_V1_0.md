# Demand Intelligence Enhancement Foundation v1.0

Status: frozen for Sprint 054

## Purpose

Sprint 054 extends the existing Sprint 053 Business Demand Intelligence foundation. It does not
replace Opportunity Discovery with forecasting and does not create a parallel intelligence system.

The preserved flow is:

Demand Signals → Demand Intelligence → Opportunity Discovery → Product Evaluation → Commerce
Execution.

Demand Intelligence strengthens the evidence base available to Opportunity Discovery. It never
creates a Product, Opportunity, sourcing decision, inventory action, campaign, approval, or
execution instruction.

## Five evidence families

Demand Intelligence consists of:

1. **Observed Demand Signals** — directly captured external, manual, news, environmental, or event
   observations.
2. **Customer Voice Signals** — GrowthOS conversations, Reddit discussions, objections, support
   language, and other direct expressions of customer pain.
3. **Marketplace Signals** — Amazon/Etsy reviews, competitor reviews, and supplied marketplace
   movement observations.
4. **Trend Signals** — search, social, event, and seasonal direction observed over a stated window.
5. **Predictive Demand Signals** — forecast metadata with explicit assumptions, timeframe,
   confidence, evidence, and uncertainty.

All five contribute evidence. None independently creates a business action.

## Source metadata

The existing tenant-scoped `DemandSignalSource` registry is extended with:

- `source_category`: customer voice, marketplace, search, social, news, weather, seasonality,
  research, or manual;
- `geographic_scope`;
- `time_window`; and
- `trend_type`: rising, falling, stable, volatile, or seasonal.

Existing source identity, collection method, evidence origin, lifecycle, and credential-free
configuration remain unchanged. Future-compatible source types include Reddit, Amazon and Etsy
reviews, Google Trends, social comments, news/events, weather/environment, and seasonal patterns.

## Predictive evidence contract

`PredictiveDemandMetadata` is optional and belongs to exactly one Demand Signal. It records a
prediction type, forecast window, confidence, non-empty assumptions, and uncertainty notes. The
metadata and its source evidence are append-only.

A prediction is evidence about a possible future condition. For example, a 72% long-range heat-risk
indicator is not a claim of guaranteed product success. Predictive evidence stays `draft` until it
passes the same human review and Governance controls as every other Demand Signal.

## Multi-signal theme analysis

`DemandThemeAnalysis` combines reviewed Demand Signals without modifying them. It deterministically
records:

- total evidence count;
- the number of independent source types;
- arithmetic-mean confidence; and
- an explainable evidence-strength label.

Strength is based on source diversity:

- one independent source type: `weak`;
- two independent source types: `medium`;
- three or more independent source types: `strong`.

This label measures evidence diversity only. It is not an Opportunity score, commercial forecast,
approval, or execution recommendation. Duplicate signal identifiers are collapsed and cross-tenant
or unreviewed signals are rejected.

## Dashboard

The existing Demand Intelligence Dashboard adds:

- signal-source distribution as counts and percentages;
- emerging themes with category, evidence count, signal diversity, confidence, and strength;
- predictive indicators with trend, timeframe, evidence references, confidence, and uncertainty;
- existing source volume, emerging categories, customer pain clusters, and reviewed pain signals.

All views are authenticated, tenant scoped, read-only projections.

## AI boundary

Existing governed AI capabilities may classify, cluster, summarize, and extract customer language
from cited evidence. AI cannot invent demand, conceal assumptions or uncertainty, create Products or
Opportunities, approve signals, execute sourcing, alter inventory, create campaigns, or initiate
Commerce execution.

## Security and audit

Authentication, organization scope validation, RBAC, audit logging, immutable evidence, and
Governance approval remain mandatory. Theme creation and predictive evidence ingestion are audited
as evidence-only actions, explicitly recording that no Product or Opportunity was created.

## Explicit exclusions

No predictive product-success engine, automatic Opportunity creation, autonomous agent, external
provider call, sourcing, inventory action, campaign, publishing, payment, customer contact, or other
execution is included.
