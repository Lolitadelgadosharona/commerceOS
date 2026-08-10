# Customer Intelligence Foundation v1.0

Status: Sprint 003 implementation contract

## Purpose

Customer Intelligence converts permitted customer evidence into traceable signals, explicit clusters, and evidence-backed insight records. It does not own customers, execute business actions, or treat external platforms as canonical sources.

## Data flow

1. A `SignalSource` registers an organization-scoped channel type. Supported V1 types are Reddit, Amazon review, Etsy review, Shopify, email, social, support, and B2B conversation. Registration does not connect to any provider.
2. `SignalService` accepts a source reference, optional in-scope customer ID, content reference, explicit signal type, sentiment, severity, and confidence. Content remains behind a reference; the signal row stores classification metadata and lineage.
3. `ClusterService` groups an explicit set of same-organization signal IDs. Membership is stored separately, duplicates are removed, count is derived, and default severity is the maximum member severity. Trend direction is supplied input, not inferred.
4. `InsightService` creates a human- or rule-supplied title, summary, impact, and recommended action from an explicit same-organization evidence set. Evidence count is derived and evidence membership is stored separately.

## Taxonomies

- Signal types: quality concern, delivery delay, price objection, trust concern, feature request.
- Sentiment: positive, neutral, negative, mixed.
- Severity/impact: low, medium, high, critical.
- Trend: increasing, stable, decreasing, unknown.
- Insight status: new, validated, actioned, dismissed.

Taxonomies are closed V1 API contracts. Expanding them requires a schema/API compatibility review rather than accepting arbitrary classifications.

## Ownership and boundaries

Intelligence owns sources, signals, clusters, memberships, insights, and evidence links. Operations remains the source of truth for `Customer`; the shared tenant-reference validator checks customer scope without importing Operations repositories. Other domains consume authorized APIs/events and cannot write Intelligence tables directly.

There are no connectors, network retrieval jobs, scraping, LLM prompts, AI summaries, embeddings, autonomous clustering, or agent actions. `content_reference` must point to evidence managed under the Security and Privacy Foundation; raw sensitive content should not be duplicated into signal metadata.

## API surface

All resources use `/api/v1`:

- `/signal-sources`
- `/customer-signals`
- `/customer-clusters`
- `/customer-insights`

Create/list/get operations are available for all four resources. Sources may be updated/deactivated; insights may transition status. Signals, memberships, and evidence links have no update/delete API in V1 so provenance is not silently rewritten.

## Activation limitations

The Sprint 002 internal authentication limitation still applies. These endpoints must not be publicly deployed until verified authentication and endpoint-wide authorization are implemented. Retention schedules, purpose-based access, and audit/event publication remain production activation gates.
