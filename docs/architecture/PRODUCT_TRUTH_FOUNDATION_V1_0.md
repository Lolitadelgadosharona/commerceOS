# Product Truth Foundation v1.0

Status: Sprint 006 implementation contract

## Purpose and ownership

Build owns `Product`, versioned `ProductTruth`, and product knowledge. This is the authoritative internal product layer. Intelligence `ProductHypothesis` remains advisory and cannot create or mutate these records. Governance owns approvals and human authority; Build consumes a narrowly verified approval fact before publishing truth.

The foundation creates no listing, storefront, advertising, support, sales, creative, LLM, agent, or external-integration behavior.

## Product lifecycle

Products begin as `draft`. Direct transition to `approved` is prohibited. An approved Governance request for the exact organization, product, and `product_truth.publish` action permits one Product Truth publication. Initial publication changes the product to `approved`. An approved product with Product Truth may become `active`; any non-archived product may become `archived`. Archived products cannot transition.

Approval identity and Product Truth creation are audit logged. The current temporary actor-header limitation remains, so no endpoint may be publicly deployed until real authentication is activated.

## Product Truth

Each Product Truth release contains a human-authored summary, features, specifications, approved claims, restricted claims, usage notes, creator, and approval lineage. Versions are positive, monotonically increasing integers unique per product. An approval request can publish only one truth version.

Product Truth is append-only in V1. Corrections require a new approved version; prior releases remain auditable. `created_by` identifies the publishing actor, while `approval_id` proves the separate human authority decision.

## Knowledge and claim policy

`ProductKnowledgeItem` holds typed feature, FAQ, objection, limitation, use-case, or care-instruction content with confidence, approval status, and optimistic version auditing. It does not supersede Product Truth.

`ProductClaimPolicy` is an organization- and brand-scoped guardrail for claim types such as medical, performance, and guarantee claims. It records whether the claim is allowed, why, and whether evidence is required. A policy does not itself approve a Product Truth claim; publication still requires the approval workflow.

## API

The `/api/v1` resources are:

- `/products`
- `/product-truth`
- `/product-knowledge`
- `/product-claim-policies`

Product approval requests use `/products/{product_id}/approval` and are decided through the existing Governance approval endpoint.
