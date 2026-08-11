# AI Discovery Listing Intelligence Foundation v1.0

Status: frozen for Sprint 026 implementation

## Purpose

This foundation prepares approved products for human conversion review and AI discovery. It structures listing strategy and evidence, assesses coverage, and identifies missing information. It does not generate listing copy, publish content, activate Shopify, distribute ads, or execute an AI model.

## Ownership and authority

- Build owns Product and Product Truth. Sprint 026 reads them through shared metadata projections and never changes them.
- Decision owns listing blueprints, GEO knowledge recommendations, listing quality assessments, and AI discovery readiness recommendations.
- Growth owns future distribution and publishing execution.
- Finance owns economics.
- Governance owns approvals.

All records are organization-scoped and reference an approved or active Build Product. A score or `ready_for_human_review` recommendation is advisory and grants no publishing authority.

## Listing blueprint

A blueprint records title strategy and structured benefit, feature, FAQ, trust, and comparison guidance plus confidence. Structures are supplied evidence and planning inputs; Sprint 026 performs no content generation.

## GEO knowledge asset

A GEO asset describes the product entity, attributes, use cases, customer questions, and answer structure. Every asset requires an evidence reference so downstream human review can trace the proposed knowledge structure to trusted source material.

## Listing quality v1

Quality is computed from five deterministic components:

- Product Truth coverage: 20 points each for summary, features, specifications, approved claims, and usage notes.
- Customer-language coverage: 25 points per traceable product objection, capped at 100.
- GEO coverage: equal coverage across entity description, attributes, use cases, customer questions, answer structure, and evidence reference.
- Trust coverage: 50 points for blueprint trust elements and 50 for approved Product Truth claims.
- Conversion coverage: equal coverage across title, benefit, feature, FAQ, trust, and comparison structures.

`overall = truth × 25% + customer language × 20% + GEO × 20% + trust × 15% + conversion × 20%`.

All scores are bounded from zero to 100. Assessments are immutable snapshots and do not alter source evidence.

## AI discovery readiness

The latest listing quality assessment supplies the coverage score. Components below 70 are named in `missing_information`.

- Coverage at least 80 with no missing component: `ready_for_human_review`.
- Coverage at least 60 with gaps: `improve_missing_information`.
- Lower coverage: `insufficient_evidence`.

Readiness is a recommendation for human review only. It does not assert that any AI system has indexed, understood, endorsed, or ranked the product.

## API boundary

- `/api/v1/listing-blueprints`
- `/api/v1/geo-assets`
- `/api/v1/listing-quality-assessments`
- `/api/v1/ai-discovery-readiness`

The API exposes advisory evidence capture, deterministic assessment, and organization-scoped reads. It exposes no generation, publish, advertise, approve, or execute route.

## Explicit exclusions

No Shopify, listing publishing, LLM generation, ads, agents, Product Truth mutation, approval creation, or distribution execution is included.
