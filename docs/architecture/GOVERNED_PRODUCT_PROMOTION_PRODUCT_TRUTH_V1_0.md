# Governed Product Promotion and Product Truth v1.0

Status: Frozen for Sprint 072

Owner: Build and Governance

Decision input owner: Intelligence

## Purpose

This contract defines the controlled boundary between an Intelligence-owned `ProductHypothesis` and a Build-owned `Product`. Investment approval authorizes pursuit of an opportunity; it does not create a Product. Product promotion requires a separate human approval and explicit execution. A created Product remains distinct from approved, versioned Product Truth.

## Canonical lifecycle

`Market evidence → MarketOpportunity → ProductHypothesis → investment approval → promotion readiness → promotion approval → Product → ProductTruthDraft → truth publication approval → ProductTruth version`

The following boundaries are invariant:

- Investment approval does not create a Product.
- Promotion approval alone does not execute Product creation.
- Product creation does not approve Product Truth.
- Product Truth publication does not publish a listing or perform Shopify execution.

## Promotion ownership and relationship

`ProductPromotion` is the normalized, tenant-scoped relationship. It records the source hypothesis, source opportunity, selected brand, promotion approval, resulting Product, requester, executor, and timestamps. The unique `(organization_id, product_hypothesis_id)` constraint permits one canonical promotion per hypothesis. The Product link is unique and is never inferred from names.

The API exposes both directions:

- Hypothesis to promotion and promoted Product.
- Product origin to promotion, ProductHypothesis, and source MarketOpportunity.

## Readiness policy

The backend projection classifies persisted conditions as blocker, warning, or information. Required investment approval, critical economics inputs, and unresolved critical ProductRisk records are blockers. Legacy numeric economics without provenance, missing opportunity evidence, and weak supplier assumptions are warnings. Warnings remain visible but do not fabricate a blocking policy.

## Deliberate promotion mapping

| Source value | Treatment | Product destination |
| --- | --- | --- |
| Hypothesis name | Initial canonical value | `Product.name` |
| Solution description | Provisional Build description | `Product.description` |
| Opportunity category | Initial canonical value | `Product.category` |
| Human-selected tenant brand | Explicit governed input | `Product.brand_id` |
| Target customer, market, problem | Reference only | Remain on ProductHypothesis |
| Economics | Reference only | Remain Intelligence assumptions; never Finance truth |
| Supplier candidates | Reference only | Never become approved suppliers |
| Risks | Reference only and remain visible | Never copied into Product truth |

## Product Truth

`ProductTruthDraft` is editable review material and is not canonical truth. A separate `product_truth.publish` ApprovalRequest is required. Explicit human publication calls the existing ProductTruth service, which creates an immutable version using the next integer version. The approval ID, creator, timestamps, draft change reason, supporting evidence, and audit record preserve review context. Approved versions are never overwritten.

The deterministic comparison only compares schema-compatible fields: ProductHypothesis name to Product name, and solution description to ProductTruth summary. Customer, economics, supplier, and risk fields are explicitly reported as non-comparable rather than guessed.

## Legacy economics provenance

Migration 0072 adds field-level provenance for legacy ProductEconomics values only when a metric has no existing provenance row. It preserves the numeric value, uses classification `legacy_unprovenanced`, source `legacy_product_economics`, null confidence/evidence/as-of fields, and an explicit no-source note. Re-running the migration logic is idempotent by economics/metric identity. No value becomes actual, quoted, or observed.

## Security, audit, and concurrency

All routes use existing authenticated actor middleware, organization scope, RBAC route policy, and resource ownership checks. Promotion and Product Truth publication record audit events. Human identity is required for Truth publication. Database uniqueness prevents duplicate canonical relationships, and promotion execution locks the relationship row before creating the Product to protect simultaneous execution.

## Next boundary

After approved Product Truth, the next missing execution boundary is governed supplier/build readiness: validating that an approved supplier can produce the canonical specification. It is intentionally not implemented in Sprint 072.
