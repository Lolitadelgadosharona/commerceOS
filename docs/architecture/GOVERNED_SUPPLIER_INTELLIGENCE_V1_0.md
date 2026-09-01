# Governed Supplier Intelligence v1.0

Status: frozen for Sprint 073

## Purpose and ownership

Supplier Intelligence turns an approved Product and its current Product Truth into an evidence-backed supplier qualification and a human supplier-selection decision. Intelligence owns evidence, quotes, evaluations, risks, matches, and deterministic qualification. Build owns Product and Product Truth. Governance owns approval. Finance owns actual monetary truth. Operations may later own procurement execution; Sprint 073 creates no purchasing authority.

## Canonical flow

`Product Truth → Supplier evidence and quote → Qualification → Comparison → ApprovalRequest → ApprovedProductSupplier → Product Supply Readiness`

`SupplierCandidate` remains an early Intelligence reference linked to a Product Hypothesis. It is not a canonical supplier and does not represent approval. `SupplierProfile` is the canonical supplier entity. `ProductSupplierMatch` records evaluated fit and supports multiple suppliers per Product. `ApprovedProductSupplier` is the canonical governed relationship, with primary, backup, or alternate role.

## Evidence and quote provenance

Every material supplier field can carry field name, value, classification, source, confidence, as-of time, evidence reference, and notes. Classifications distinguish observed, supplier-claimed, quoted, verified, assumption, AI inference, and unknown. Unknown values remain unknown.

Supplier quotes preserve currency, unit price, MOQ, price tiers, sample/tooling/packaging costs, Incoterm, payment terms, lead time, validity, classification, source, and confidence. A quoted unit price may populate the existing product-economics provenance ledger as `quoted`; it remains advisory cost evidence and is not Finance actual cost.

## Qualification and readiness

The deterministic qualification projection covers product fit, commercial fit, quality, capacity, lead time, compliance, logistics, payment terms, supplier reliability, and provenance quality. Each dimension reports pass, conditional, fail, or unknown with evidence and gaps. Missing data never receives a fabricated score.

Approval may be requested only when no blocker or failed dimension remains. Warnings and unknowns remain visible for human judgment. Product Supply Readiness requires governed Product origin, current Product Truth, at least one approved Product-Supplier relationship, and no open critical supplier risk.

## Authority boundaries

Supplier approval means only that a supplier is approved as a candidate for a specific Product and role. It does not authorize outreach, negotiation, purchase orders, payments, inventory, freight, listing, channel launch, or autonomous execution. Service identities cannot exercise human approval authority. All records and projections are organization scoped.

## Compatibility

Legacy direct Products remain readable but are blocked from supply readiness until a governed promotion origin exists. Existing generic `SupplierProfile.status=approved` remains lifecycle metadata and is not equivalent to Product-specific governance. The Sprint 072 promotion request is now transactionally composed with its approval and queue records to prevent an orphaned approval during a concurrent request race.
