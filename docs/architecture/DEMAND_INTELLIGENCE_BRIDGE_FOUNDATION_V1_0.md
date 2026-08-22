# Demand Intelligence Bridge Foundation v1.0

Status: frozen for Sprint 052

## Purpose

The bridge converts human-accepted GrowthOS conversation learning into traceable demand-signal
candidates for CommerceOS Intelligence. A demand signal is evidence of a recurring customer
problem. It is not a product, opportunity, decision, approval, or execution instruction.

## Ownership and dependency boundary

- Growth owns conversations, objections, customer language, sales outcomes, and their learning
  signals.
- Intelligence owns demand signals, their evidence, aggregation, and market interpretation.
- Decision may consume reviewed evidence to prepare recommendations.
- Governance owns approval authority.
- Build, Operations, Growth, and Finance source truth cannot be changed through this bridge.

The Intelligence implementation reads Growth-owned tables through shared persistence metadata;
it does not import or write Growth domain models. The application layer exposes the composed API.
No parallel AI runtime, learning engine, or product engine is introduced.

## Evidence lifecycle

1. A human reviews and accepts a governed conversation analysis.
2. Growth creates one or more evidence-linked sales learning signals through the Sprint 042
   Learning Loop.
3. A permitted human selects those accepted signals and supplies a segment and category.
4. Deterministic aggregation creates a `draft` demand signal and immutable evidence rows.
5. Human review may move the signal to `review` or `rejected`.
6. Moving from `review` to `approved` requires a matching approved Governance request.

Terminal approved and rejected records cannot re-enter the workflow. Approval means the evidence
is accepted for intelligence use; it does not authorize opportunity or product creation.

## Deterministic aggregation contract

The service accepts only tenant-matched learning signals whose source conversation analysis is
`accepted`. It rejects missing, cross-tenant, unreviewed, or empty source evidence.

- `frequency` and `evidence_count` equal the selected evidence-row count.
- `confidence` is the arithmetic mean of source confidence values, rounded to four decimals.
- `problem_statement` is the stable, deduplicated sequence of source insights.
- `customer_language` is the stable, deduplicated sequence of original customer replies.
- `source_reference_id` is the stable lowest learning-signal identifier.

The bridge does not infer absent facts, fabricate language, or create an opportunity or product.
AI Runtime capabilities may later classify, cluster, summarize, or extract language, but outputs
must remain cited candidates under the same review boundary.

## Data and API contract

`demand_signals` is tenant scoped and records lineage, segment, category, customer problem and
language, observed frequency, confidence, evidence count, and review status.
`demand_signal_evidence` is tenant scoped and append-only; each row identifies its Growth learning
source and preserves the original customer evidence.

Authenticated `/api/v1` endpoints provide signal creation/listing, evidence listing, controlled
status review, and a read-only dashboard. The dashboard shows reviewable or approved customer
pains, frequency, segment, confidence, evidence count, and source-conversation references.

## Security and audit

Universal authentication, organization validation, RBAC, and domain authorization apply to every
endpoint. Mutations record the human actor, tenant, resource, result, and evidence-only authority.
Governance approval must match the signal, tenant, object type, and action. Service or AI identity
cannot confer human approval authority.

## Explicit exclusions

No automatic opportunity or product creation, sourcing, customer contact, message sending,
external connector, autonomous agent, financial commitment, or execution workflow is included.
