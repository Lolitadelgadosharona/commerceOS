# Business Demand Intelligence Foundation v1.0

Status: frozen for Sprint 053

## Purpose

Business Demand Intelligence is the shared evidence layer between external market sensing,
GrowthOS customer learning, CommerceOS research, and later Opportunity Intelligence.

CommerceOS discovers demand independently. GrowthOS contributes additional customer evidence; it
is not the exclusive source of CommerceOS opportunities.

External market signals + GrowthOS customer signals + CommerceOS research signals flow into one
Business Demand Intelligence layer. Reviewed demand may later inform Opportunity Intelligence,
CommerceOS product decisions, or GrowthOS revenue execution through their own authority boundaries.

## Ownership

Intelligence owns source registration, evidence ingestion, aggregation, traceability, clustering
projections, and demand confidence metadata. It does not own Products, Opportunities, approvals,
sourcing, financial commitments, or execution.

Growth continues to own customer conversations and outcomes. External connector domains own their
raw records. Research owns cited analysis. Business Demand Intelligence copies or references
evidence without modifying those sources of truth.

## Source abstraction

`DemandSignalSource` is a tenant-scoped registry record describing:

- source type and display identity;
- owning source domain;
- collection method;
- evidence origin; and
- active lifecycle state.

Supported V1 source types are `growthos_conversation`, `reddit`, `amazon_review`, `etsy_review`,
`google_trend`, `social_comment`, `competitor_review`, `research_analysis`, and `manual_input`.
Registry configuration contains metadata only and never stores credentials.

Generic ingestion requires an active tenant-matched source registration. The existing Sprint 052
GrowthOS aggregation path remains compatible and ensures its built-in source registration exists.

## Demand signal contract

Every Demand Signal now records:

- `source_type` and external `source_reference`;
- `collection_method` and `evidence_origin`;
- explicit `confidence_basis`;
- customer segment, category, problem, and original customer language; and
- frequency, confidence, evidence count, and human-review status.

Each evidence row retains a local source identifier, external source reference, source type, and
evidence text. Evidence is append-only. Signal frequency and evidence count equal the supplied
evidence rows; empty or unregistered sources are rejected.

Sprint 052 fields remain intact for compatibility. Existing records are migrated with explicit
legacy GrowthOS provenance, while all new records receive precise source metadata.

## GrowthOS compatibility

Only human-accepted GrowthOS conversation analyses may enter deterministic aggregation. The signal
uses `growthos_conversation`, preserves every learning-signal reference and original reply, and
calculates confidence as the arithmetic mean of accepted learning confidence. No existing Sprint
052 review, approval, audit, or API behavior is removed.

## External and research compatibility

External and research evidence enters through the same registered-source contract. The ingestion
layer does not scrape, call providers, interpret missing facts, or automatically create insights.
Source systems must supply stable local evidence IDs, external references, evidence text, and an
explainable confidence basis.

## Dashboard projection

The Demand Intelligence Dashboard adds:

- signal and evidence volume by source;
- average confidence by source;
- emerging categories ranked by observed frequency;
- reviewed customer pain statements; and
- source references for every displayed signal.

These are read-only evidence projections, not opportunity or product decisions.

## AI boundary

The existing Governed AI Runtime may classify, cluster, summarize, or extract customer language
from cited evidence. AI cannot invent demand, omit provenance, approve signals, create Products or
Opportunities, execute sourcing, contact customers, or initiate revenue execution.

## Security and governance

Universal authentication, organization scope validation, RBAC, audit logging, immutable evidence,
and Governance-controlled approval remain mandatory. Every mutation records evidence-only
authority and explicitly records that no Opportunity or Product was created.

## Explicit exclusions

No Product or Opportunity creation, autonomous approval, sourcing, external execution, provider
call, customer contact, financial commitment, or new AI or Learning runtime is included.
