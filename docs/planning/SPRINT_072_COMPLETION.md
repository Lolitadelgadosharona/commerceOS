# Sprint 072 Completion — Governed Product Promotion and Product Truth

## Outcome

Sprint 072 establishes a controlled ProductHypothesis-to-Product transition and operationalizes Product Truth drafts, independent review, explicit publication, immutable versions, provenance warnings, and traceable UI states. No Shopify, supplier contact, listing publication, payment, or autonomous approval was added.

## Architecture decisions

- Reused the existing Build-owned Product and versioned ProductTruth models.
- Added ProductPromotion as the canonical relationship and governance record rather than adding a duplicate Product concept.
- Kept investment approval, promotion approval, promotion execution, Truth review, and Truth publication as distinct steps.
- Kept economics, suppliers, risks, customer, and market assertions attached to Intelligence records instead of copying them into Product Truth.
- Added `legacy_unprovenanced` to preserve legacy numeric economics without fabricating source quality.

## Product lifecycle mapping

| Arrow | Classification |
| --- | --- |
| Market evidence → Opportunity | Direct |
| Opportunity → ProductHypothesis | Direct |
| ProductHypothesis → investment decision | Indirect through its source Opportunity |
| Investment decision → promotion readiness | Direct projection |
| Promotion readiness → promotion decision | Direct governed request |
| Promotion decision → Product | Direct explicit execution |
| Product → ProductTruth | Direct through separately approved ProductTruthDraft |

Supplier/build readiness after Product Truth remains missing and is the next boundary for product execution.

## Migration behavior

Migration `0072_governed_product_promotion` creates promotion and Truth draft tables and backfills only missing legacy economic metric provenance. Downgrade removes only migration-marked legacy rows before dropping the new tables.

## Validation evidence

Focused backend tests cover the complete promotion and Product Truth chain, idempotency, tenant isolation, and version behavior. Sprint 071 provenance/committee regressions remain included. The dedicated Sprint 072 Playwright suite contains 20 acceptance cases spanning Opportunity, Product, Decision Committee, Growth regression, and no-Shopify boundaries. Exact final results are recorded in the delivery report.

## Known limitations

- The legacy direct Product creation endpoint remains for compatibility and is not the canonical promotion path.
- Promotion request creation uses the existing ApprovalWorkflow service, whose internal commit can leave a superseded orphan approval under a rare concurrent first-request race; the canonical promotion and Product remain protected by uniqueness and row locking.
- Supplier readiness and Build readiness are visible future stages, not implemented execution.
