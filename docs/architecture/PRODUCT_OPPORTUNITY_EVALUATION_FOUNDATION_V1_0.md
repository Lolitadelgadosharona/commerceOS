# Product Opportunity Evaluation Foundation v1.0

Status: frozen for Sprint 056 implementation

## Mission and ownership

The Intelligence domain converts a human-accepted Opportunity Candidate into one or more advisory
Product Candidates. It reuses Opportunity Discovery provenance, the governed AI Runtime boundary,
Learning extension points, authentication, RBAC, audit logging, and Governance approvals. The
repository's canonical `organization_id` remains the tenant boundary.

An Opportunity Candidate describes a market problem supported by demand evidence. A Product
Candidate describes one possible solution direction that still requires validation. Neither is an
approved Product or Product Truth.

## Evidence requirements

Every evaluated Product Candidate requires at least one same-tenant, entity-backed evidence link.
Supported references are Demand Signals, Opportunity Evidence, marketplace evidence, customer
conversations, and research analysis. Product Candidate Evidence is append-only and records the
source, source identity, summary, relevance, and confidence.

Evidence supports a hypothesis; it does not prove demand, margin, safety, supplier suitability, or
commercial success. Assumptions, weaknesses, risks, and missing information remain explicit.

## Deterministic evaluation methodology

V1 uses the versioned and explainable formula:

- demand fit: 25%;
- problem-solution fit: 25%;
- estimated gross margin: 20%;
- shipping simplicity: 15%;
- inverse average fulfillment, IP, regulatory, payment, and dispute risk: 15%.

Risk bands map to `low=100`, `medium=70`, `high=40`, and `critical=10`. Scores at or above 65 yield
“Suitable for further validation”; lower scores request more evidence. This recommendation is not a
launch, sourcing, inventory, or spending decision. Price, cost, and margin fields are estimates;
Finance remains authoritative for monetary truth.

## Lifecycle and human decisions

Candidates move through `draft`, `under_review`, `accepted`, `rejected`, and `archived`. Creation
requires an accepted Opportunity Candidate. Product Candidate acceptance requires an approved
same-tenant Governance request. No system or AI output can approve itself.

The next human decisions are whether to validate the hypothesis and whether later evidence merits
Supplier Intelligence. Sprint 056 does not contact suppliers, select MOQ, place orders, manage
inventory, create Product Truth, publish content, launch advertising, or spend money.

## Interfaces and future extension points

Authenticated APIs expose candidate creation/listing/retrieval, evaluation, evidence, review, and a
read-only dashboard for candidate products, economics assumptions, risks, and the validation queue.
Candidate identity and provenance allow future Supplier Intelligence, Creative Intelligence,
GrowthOS customer validation, and Learning outcomes without granting those future consumers write
authority over this evidence.

The system can answer **what product directions might solve a validated market opportunity**. It
cannot answer **what inventory should be purchased tomorrow**.
