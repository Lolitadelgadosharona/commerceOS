# First Revenue Machine Prospect Discovery Foundation v1.0

Status: frozen for Sprint 061 Product Review

## Purpose

Sprint 061 turns the existing GrowthOS discovery and revenue capabilities into a founder-operated
daily prospect workflow for independent Beauty businesses:

Controlled source → Prospect candidate → Traceable evidence → Qualification → Growth Profile →
Growth Opportunity → Growth Gift → Outreach draft → Human review.

It does not crawl the public web autonomously, send messages, sell, negotiate, or collect payment.

## Source adapter contract

`ProspectDiscoverySource` remains the provider-neutral registry. Each source now identifies an
`adapter_key` and one controlled collection mode:

- `human_review`: the founder records reviewed public evidence.
- `controlled_import`: a bounded import supplies already collected evidence.
- `controlled_connector`: a future authenticated connector operates under explicit controls.

Current contracts support Website, Google Business Profile, Instagram, and Manual Import. TikTok,
Reddit, Yelp, Google Trends, News, and Other are compatible source identities only. No new network
adapter or crawler is included.

## Evidence snapshots

Three append-only, tenant-scoped structured evidence records complement the existing generic
Prospect Research Evidence:

- `WebsiteEvidenceSnapshot`: business identity, services, site structure, homepage, booking, SEO,
  and GEO visibility observations.
- `BusinessProfileEvidenceSnapshot`: observed reviews, rating, location, category, and customer
  language.
- `InstagramEvidenceSnapshot`: observed profile information, posting frequency, content themes,
  and brand signals.

Every snapshot preserves its registered source, source reference, capture time, and confidence.
Updates and deletes are rejected. Missing observations remain absent; collectors cannot fabricate
values.

## Qualification and pipeline

The existing deterministic qualification service remains controlling. Missing inputs continue to
withhold the score. The pipeline endpoint is a read-only projection over existing records; it
reports the next founder action without creating a Prospect, Profile, Opportunity, Gift, or Draft.

Existing services retain their ownership:

- Discovery owns candidates and source evidence.
- Growth owns Growth Profiles, advisory Opportunities, Gifts, and outreach drafts.
- Industry Intelligence supplies reusable Beauty patterns.
- Governance owns external communication approval.
- Sales Copilot supplies advisory analysis and drafts.
- Finance owns revenue truth.

## Operator dashboard

The founder dashboard reports business activity rather than infrastructure health:

- prospects discovered today;
- qualified prospects;
- growth opportunities;
- Gifts ready;
- outreach drafts awaiting or holding approval;
- replies and positive conversations;
- open revenue experiments;
- estimated AI cost from AI Runtime observations.

The dashboard is read-only. It does not infer revenue or trigger any workflow transition.

## AI routing and authority

The existing provider-neutral model policy remains authoritative: extraction and classification
may use low-cost policies; opportunity reasoning may require higher quality; customer-facing drafts
may require the highest reviewed quality. Estimated cost comes from AI Runtime observations. No
provider call is introduced by this sprint.

Authentication, RBAC, tenant isolation, audit logging, evidence ownership, and human approval remain
mandatory.

