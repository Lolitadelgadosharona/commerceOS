# Listing Intelligence and GEO Foundation v1.0

Status: Sprint 008 implementation contract

## Purpose and ownership

Build owns product-grounded listing strategy, content briefs, discovery knowledge, customer question maps, and listing evidence as construction artifacts. Product Truth remains authoritative. Growth and future channel executors may consume approved artifacts but cannot use them to modify Product Truth or bypass Governance.

These structures are planning and knowledge records only. They contain no copy generation, SEO/GEO automation, publishing, storefront, ad, LLM, or agent capability.

## Structures

- `ListingStrategy` records target customer, value proposition, positioning, and differentiation. One current strategy exists per product.
- `CustomerQuestion` records buying, trust, delivery, quality, usage, or objection questions with source reference and 0–100 importance.
- `ProductDiscoveryKnowledge` represents product, use-case, audience, problem, solution, and feature entities plus explicit relationships and confidence.
- `ContentBrief` records human-authored headline direction, benefits, proof points, objections, and trust elements. Multiple appendable/version-audited briefs may coexist.
- `ListingEvidence` records customer quotes, review insights, specifications, or supplier evidence with provenance and confidence.

All resources are organization-scoped and must reference a Build Product in that organization. Specification evidence must reference a Product Truth UUID for that exact product.

## Lifecycle and authority

Listing strategies move `draft → approved → active → archived`, with early archival allowed. Approval requires at least one Product Truth release. This is internal content-strategy approval, not permission to publish. An archived strategy cannot transition.

Content cannot establish a new product claim. Claims absent from Product Truth remain unapproved regardless of their appearance in a brief, evidence item, or discovery relationship.

## GEO foundation

The discovery graph stores explicit, confidence-scored entity relationships so future systems can answer product, audience, problem, solution, feature, and use-case questions with traceable facts. V1 does not perform retrieval optimization, schema markup, indexing, ranking, generation, or external submission.

## API and exclusions

The `/api/v1` resources are `/listing-strategies`, `/customer-questions`, `/product-discovery-knowledge`, `/content-briefs`, and `/listing-evidence`.

There is no Shopify, SEO publishing, GEO automation, AI copywriter, LLM, advertising, automated listing generation, or external integration. Public deployment remains prohibited until authentication activation is completed.
