# Discovery Automation Layer v1.0

Status: frozen for Sprint 062 Product Review

## Purpose

The Discovery Automation Layer turns the Sprint 061 controlled acquisition foundation into a
repeatable daily Beauty discovery workflow:

Industry + geography + controlled source → Discovery run → Public evidence → Qualification →
Ranked prospect → Existing opportunity and Growth Gift workflow.

Automation schedules work and records evidence. It does not create an unrestricted crawler,
contact a prospect, negotiate, approve, or collect payment.

## Automation plans and runs

`DiscoveryAutomationPlan` binds one tenant-scoped controlled connector source to an industry,
geography, explicit query criteria, and daily cadence. Starting a plan creates an existing
`ProspectDiscoveryRun`, preserves the plan and query provenance, and moves it to `running`.

The supported core lifecycle is `draft → running → completed | failed`. Existing queued and
cancelled states remain backward compatible. Runs preserve start/end time, query criteria, source,
and observed result count. Starting a run does not itself make a provider call.

## Google Business discovery

`GoogleBusinessDiscoveryResult` records bounded public business observations supplied by a
registered Google Business controlled connector:

- business name, category, location;
- optional rating, review count, and website;
- public profile metadata;
- source reference, capture time, and confidence.

Each result creates or reuses a deduplicated Prospect Candidate through the existing Discovery
service. Missing rating, review count, website, and profile values remain null or absent. Results
are immutable and cannot trigger outreach.

## Website and social intelligence

Sprint 061 Website and Instagram evidence snapshots remain controlling. They capture homepage,
booking, service clarity, SEO, GEO, trust, bio, posting activity, content themes, and brand
observations as evidence only. Sprint 062 does not add a separate crawler or posting system.

## Ranking

The daily ranked prospect view reads the existing deterministic Qualification Assessment. It does
not introduce a second scoring engine. Ranking factors remain growth pain, purchase probability,
accessibility, and quick-win potential. If an input is missing, the score remains null and the
missing inputs remain visible.

## Prospect memory

`ProspectMemoryEvent` is an append-only record of observed Website, social, review, location, or
business-event change. Each event preserves previous and observed state, source, time, and
confidence. Equal before/after observations are rejected. Memory does not overwrite earlier
evidence or mutate business truth.

## AI cost routing

Existing provider-neutral GrowthOS model policies and AI Runtime cost observations remain
authoritative. Discovery and classification may select economy policies; opportunity reasoning and
customer draft preparation may select higher-quality policies. No provider is hardcoded and this
sprint adds no provider execution.

## Authority boundary

- Discovery owns plans, runs, candidates, public evidence, and prospect history.
- Existing Industry Intelligence, Opportunity, Growth Gift, and Sales Copilot services remain in
  place.
- Governance owns human approval and external communication authority.
- AI may extract, classify, analyze, recommend, and draft; it cannot communicate or execute.
- Authentication, RBAC, tenant isolation, audit logging, and source provenance remain mandatory.

