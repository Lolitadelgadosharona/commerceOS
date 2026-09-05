# Governed Listing Intelligence v1.0

Status: frozen for Sprint 075

## Purpose and ownership

The Build domain owns the canonical, channel-neutral commercial representation of a governed Product. Decision-owned listing/GEO recommendations remain advisory inputs. Governance owns approval authority. Product Truth remains the product-fact source of truth; Finance remains monetary truth; Growth and future channel adapters own distribution execution.

The lifecycle is deliberately separated:

`Product Truth → Build Package → Listing Draft → Claim Review → Listing Readiness → Human Listing Approval → Approved Listing Version → Channel Projection → future Publication`

Listing Ready means that an evidence-backed commercial representation passed its review gates. It never means publication is authorized.

## Existing assets and canonical extension

The repository already contained `ListingStrategy`, `CustomerQuestion`, `ProductDiscoveryKnowledge`, `ContentBrief`, `ListingEvidence`, `ProductClaimPolicy`, listing blueprints, GEO knowledge and AI listing recommendations. These remain valid inputs or advisory models. Sprint 075 adds only the missing canonical layer: `ListingVersion`, `ListingClaim`, `ListingClaimEvidence`, `ListingFAQ`, deterministic Listing Readiness, package approval, and read-only channel projection.

## Source policy

Allowed factual sources are approved Product Truth, approved Build requirements, verified Supplier evidence, approved Product Economics for commercial decisions, approved policies, and human-approved positioning. Market/customer evidence may guide problem framing, priority, FAQ wording and positioning, but it does not prove a Product claim.

AI inference, unverified supplier assertions, expired quotes, assumptions, draft truth, unsupported competitor claims and legacy unprovenanced values cannot establish factual support. This policy is enforced in backend composition, not by prompts or frontend labels.

## Claims

Supported claim types are product fact, feature, benefit, performance, quality, material, dimension, compatibility, shipping, return, compliance, comparative, sustainability, health/safety and other. Each claim retains its Listing version, Product, classification, evidence, support state, risk, review state, actor and timestamps.

Support resolves deterministically to `supported`, `conditional`, `unsupported`, `prohibited`, or `unknown`. Unknown never passes. Restricted Product Truth and a disallowing ProductClaimPolicy produce prohibited. High-risk categories require an explicit brand policy, strong approved/verified evidence and human review. Policy does not encode a legal conclusion; it records the configured business review rule.

Features are objective facts. Benefits are customer-facing outcomes which still require support. No transformation from a feature into a performance outcome is automatic.

## Version and truth dependency

Every Listing version stores the exact Product Truth row and version used to derive it. Draft, review, approved and superseded are distinct states. Approved versions are immutable through mutation endpoints; a change creates a new version. When current Product Truth differs, the package becomes stale and requires review rather than silently changing copy.

Draft planning requires a governed Product and approved Product Truth. Build blockers prevent Listing approval; Build warnings do not. This preserves early preparation without misrepresenting approval eligibility.

## Content and FAQ

The Listing version has typed commercial sections for identity, summary, problem, solution, features, benefits, specifications, use cases, included items, care, warnings, shipping, returns, risk reversal, SEO, topics, structured attributes and explicitly classified commercial price.

FAQ answer states are supported answer, needs review, missing product fact and missing policy. A supported answer requires both content and an evidence reference. Shipping, return, warranty and trust language remain unknown until canonical policy evidence exists.

## SEO, GEO and structured readiness

SEO fields are channel neutral: title, meta description, slug suggestion, topics and FAQ. GEO means factual, extractable product data: identity, category, brand, audience/use case, specifications, attributes, price state, shipping, returns, FAQ and evidence-linked claims. No artificial AI score exists.

Structured-data readiness is an internal completeness projection only. It does not claim Google, Shopify or marketplace validity. Assumed selling price is not copied into approved Listing Truth; `price_status=approved` is required for Listing approval and projections.

## Readiness and approval

Backend blockers include missing governed origin, Product Truth, draft, unresolved Build blockers, stale truth, unsupported/unknown/prohibited required claims, unapproved price, required Listing attributes, high-risk warnings/policy, and critical source gaps. FAQ, SEO, limited customer language and optional proof are warnings unless a configured policy makes them required.

The approval flow is package-level: readiness → review request → `ApprovalRequest` plus `DecisionQueueItem` → independent human decision → explicit Listing finalization. Service identities cannot exercise human authority. Approval audit metadata explicitly records that publication is false.

## Channel projection and publication boundary

Approved Listing Truth is the source for future Shopify, Amazon, Etsy and independent-site projections. Sprint 075 exposes a read-only Shopify draft projection with no external ID, no OAuth, no API call and `publication_authorized=false`. The missing boundary is channel connection/OAuth, schema validation and mapping, media/variant completeness, idempotent external write, publication approval, execution audit, reconciliation, rollback and monitoring.

## Security and AI boundary

All APIs remain behind authentication, organization scope and RBAC. Writes require a scoped human actor and are audited at key governance transitions. Cross-tenant access is rejected. AI may later propose drafts, claims or classifications through the governed runtime; it cannot establish truth, approve a claim, approve a Listing or publish.
