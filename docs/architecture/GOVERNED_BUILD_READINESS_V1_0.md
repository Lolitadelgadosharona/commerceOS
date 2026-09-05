# Governed Build Readiness v1.0

Status: frozen for Sprint 074

## Purpose and ownership

Build Readiness answers whether a governed Product has enough product, supplier, validation, and cost evidence to prepare for commercialization. Build owns the read model and validation workflow. Build does not own supplier research, Product Truth, approvals, or actual financial truth: Intelligence owns supplier evidence; Build owns Product and Product Truth; Governance owns approvals; Finance owns actual monetary records.

Build Ready never authorizes supplier contact, a purchase order, payment, manufacturing, freight, listing publication, Shopify activation, advertising, or launch. Those remain separately governed execution boundaries.

## Canonical lifecycle

`Market Evidence → Opportunity → Product Hypothesis → Investment Approval → Product Promotion → Product → Product Truth → Supplier Intelligence → Supplier Qualification → Supplier Approval → Supply Ready → Supplier Validation → Build Package → Build Ready`

Listing Ready and Commerce Ready follow Build Ready but are intentionally outside Sprint 074. Build records retain Product-to-hypothesis and hypothesis-to-opportunity references so the customer problem and market evidence remain traceable.

## Existing-domain audit

Before Sprint 074, the repository already contained canonical `Product`, versioned `ProductTruth`, `SupplierProfile`, Product-linked supplier evidence and quotes, deterministic qualification, supplier selection approvals, `ApprovedProductSupplier`, supply readiness, Product and Supplier risks, and a quote-to-economics compatibility link through generic provenance fields.

It did not contain a Build entity, Build Package, canonical Build Readiness, explicit sample lifecycle, reusable inspection/QC artifact, Product Truth requirement records, SupplierCandidate promotion contract, or normalized SupplierQuote foreign key on economic provenance. `ProductTruth.specifications` existed as versioned JSON, but did not provide typed requirement identity and build/listing applicability. No packaging-validation domain existed. Sprint 074 therefore adds only the narrow missing contracts; it does not add manufacturing execution or listing data.

## Canonical identity promotion

`SupplierCandidate` remains immutable intelligence history. It becomes linked to a canonical `SupplierProfile` only after an authenticated human explicitly confirms either a verified existing profile or the creation of a new profile with verified identity data. Name similarity never triggers an automatic merge.

`SupplierCandidatePromotion` records organization, source candidate, canonical supplier, human confirmer, and confirmation time. The organization-and-candidate uniqueness constraint makes retries idempotent. Reusing a different canonical profile after confirmation is rejected. Every confirmation is tenant checked and audited.

## Product requirements

`ProductBuildRequirement` is a version-bound, vertical-agnostic typed fact:

- stable attribute key and display label;
- value and optional unit;
- provenance classification and evidence reference;
- required-for-build and required-for-listing flags.

The record belongs to a specific Product Truth version. It supplements the legacy structured specification object without copying vertical-specific fields into the core model. Beauty, Pet, Home, Industrial, and later vertical rules belong in configurable schemas or policy, not hard-coded columns.

Product Truth defines what must be produced. Samples, inspections, supplier responses, and Build Readiness describe whether that truth can be met; they never rewrite Product Truth.

## Supplier validation and samples

`ProductSample` records a Product/Supplier sample lifecycle without sending a request. `requested` is an internal observation only. The lifecycle supports not requested, requested, received, under review, accepted, and rejected states, with optional cost, shipping, evidence, current truth version, and actor metadata.

A structured human review records pass, conditional, fail, or unknown plus dimension results, notes, evidence, reviewer, and time. Missing review information defaults to unknown, never pass.

`SupplierValidationArtifact` is the narrow reusable inspection and validation record for a Product/Supplier and optional sample. It distinguishes supplier claims, documented evidence, sample observations, inspection results, human verification, and unknown data through provenance classification. It supports inspection type, result, observations, defect counts, evidence, verifier, and date. It is not a factory QC, batch, procurement, or certification automation system.

## Product Truth to supplier fit

The Build Package deterministically compares each current Product Truth build requirement to persisted evidence from approved suppliers. Every row contains requirement, supplier response, evidence, status, gap, and supplier identity. No supplier capability is inferred. Missing evidence remains `unknown`; conflicts or negative validation remain `fail`; qualified limitations remain `conditional`.

## Quotes and economics

`ProductEconomicInputProvenance.supplier_quote_id` provides a normalized direct relationship to `SupplierQuote`. Quote-derived values remain `quoted`, never `actual`. Writes validate organization, Product, and governed Product origin. Existing generic source/evidence fields remain readable for backward compatibility.

The Build Package exposes supplier, quote date, validity, confidence, evidence, classification, and input value. Expired quotes become warnings and do not silently become current costs. Finance remains the source of actual cost and monetary truth.

## Build Package

`GET /api/v1/products/{product_id}/build-package` is an authenticated, tenant-scoped, read-only projection. It composes, rather than duplicates:

- canonical Product and current Product Truth;
- typed build requirements;
- Product Truth-to-supplier fit;
- pending and executed approved supplier relationships;
- candidate-to-profile promotion state;
- samples and reviews;
- supplier validation and inspection evidence;
- quote-backed economics and provenance;
- packaging and compliance policy state;
- critical Product and Supplier risks;
- blockers, warnings, status, and deterministic next action;
- backward opportunity and hypothesis references.

The endpoint tolerates partial data, performs no AI call, makes no connector call, and fabricates no values. `GET /api/v1/build-packages` supplies the Product Build Control Center projection.

## Requirement policy

`BuildRequirementPolicy` is the smallest persisted, product-scoped policy boundary. It can require a sample, inspection, compliance evidence, or packaging validation and records the policy reason. A requirement becomes a blocker only when policy requires it. Frontend code never guesses whether a category requires a sample, certification, or inspection.

## Canonical readiness

Backend composition is authoritative:

- `not_ready`: at least one blocker exists;
- `conditional`: no blocker exists, but one or more warnings require review;
- `ready`: no blocker or unresolved policy warning exists.

Blockers include missing governed Product or approved Product Truth, no executed Product-Supplier relationship, missing or failed required fit, required failed/unreviewed sample or inspection, required compliance/packaging evidence, unresolved critical Product/Supplier risk, or missing critical normalized supplier-cost provenance.

Warnings include an expired or near-expiry quote, only one approved supplier, an optional unreviewed sample, and legacy non-normalized economic provenance. Warnings are not converted into blockers merely by presentation logic.

No arbitrary `mark Build Ready` action exists. The current Governance model has no narrow, expiring blocker-exception contract; Sprint 074 deliberately reports this as a missing boundary instead of adding an unsafe override.

## Governed actions and audit

The Build UI may execute an already-human-approved `ApprovedProductSupplier` relationship. Execution is tenant-safe, audited, and idempotent. It creates no contact, order, purchase, or payment.

All new reads require `api.read`; all new writes require `api.write`. Production identity comes from the verified session context. The legacy actor header is accepted only by the explicit test bypass. Audit metadata identifies actor, organization, resource, result, and the no-external-side-effect boundary.

## Deterministic next action

The first unresolved persisted prerequisite determines the next action: govern Product, approve Product Truth, promote Supplier Candidate, add supplier evidence, record a quote, execute an approved supplier relationship, record/review a sample, record inspection/compliance/packaging evidence, resolve critical risk, or review Build Package warnings. No next action performs external execution.

## Explicit exclusions

Sprint 074 adds no supplier connector, contact, negotiation, purchasing, PO, payment, manufacturing, inventory, freight, Listing Ready computation, Shopify behavior, publishing, ads, autonomous agent, or Customer 360 implementation.
