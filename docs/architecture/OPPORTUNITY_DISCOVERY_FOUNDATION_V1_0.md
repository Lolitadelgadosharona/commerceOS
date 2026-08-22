# Opportunity Discovery Engine Foundation v1.0

Status: frozen for Sprint 055 implementation

## Mission and ownership

The Intelligence domain converts reviewed, multi-source Demand Intelligence into evidence-backed
Opportunity Candidates. It reuses the Demand Signal registry, governed AI Runtime, Learning
extension points, authentication, RBAC, audit, and Governance approval system. It does not create a
parallel intelligence stack.

`organization_id` is the repository's canonical tenant boundary. Every candidate, evidence link,
assessment, query, and review is organization scoped.

## Flow

Demand Signals → deterministic aggregation → Opportunity Theme → Opportunity Candidate → human
review → future Product Evaluation.

Only demand signals that have entered human review may support a candidate. Grouping may use
category, customer problem, customer segment, geography, and trend metadata. The first version is
deterministic; governed AI may later provide cited drafts, never provenance-free creation.

## Evidence and assessment

Opportunity Evidence is append-only and links each candidate to an existing Demand Signal. Each
link records evidence type, summary, contribution, and confidence. An assessment records timing,
risks, missing information, assumptions, and explainable source diversity:

- one independent source: weak;
- two independent sources: medium;
- three or more independent sources: strong.

Confidence is the arithmetic mean of the linked signal confidence values. It is advisory rather
than a forecast of commercial success. Missing inputs remain explicit in the assessment.

## Lifecycle and human authority

Candidates move through `draft`, `under_review`, `accepted`, `rejected`, and `archived`. Acceptance
requires an approved Governance request belonging to the same organization. Rejection remains a
human review outcome. Neither outcome creates a Product or authorizes sourcing, inventory,
publishing, advertising, supplier selection, or any other execution.

The system can answer **what market opportunities are supported by evidence**. It cannot answer
**what product should be sold immediately**; that belongs to future Product Evaluation.

## API and dashboard

Authenticated `/api/v1/opportunities` creation accepts the established market-observation contract
or the evidence-backed discovery contract for compatibility. Discovery resources expose candidate
listing and retrieval, nested evidence and assessment reads, Governance-bound review, and the
Opportunity Discovery Dashboard. The dashboard projects opportunity themes, emerging candidates,
and the pending review queue without mutating source truth.

## Learning extension

Candidate IDs, evidence links, methodology version, and eventual reviewed status provide extension
points for future execution-outcome Learning Signals. Sprint 055 does not implement execution
feedback or modify the Learning domain.
