# Industry Intelligence and AI Growth Service Foundation v1.0

Status: frozen for Sprint 058 Product Review

## Purpose

Industry Intelligence accumulates evidence-backed knowledge about recurring business growth
problems, buying behavior, service outcomes, objections, seasonality, and channel patterns. Beauty is
the first target profile, not a hardcoded domain. The same contracts support Pet, Home, Industrial,
B2B, and future verticals.

## Ownership

- GrowthOS owns customer-side business intelligence, prospect analysis, Growth Gifts, service
  recommendations, outreach drafts, Sales Copilot inputs, and customer relationships.
- CommerceOS owns market-side demand and product opportunity intelligence independently.
- Shared AI Runtime, Evidence, Learning, Customer Intelligence, Knowledge, routing, and Governance
  capabilities do not transfer source-of-truth ownership between the systems.
- GrowthOS feedback may become one CommerceOS Demand Intelligence input. It is never the exclusive
  source; marketplace, consumer, social, search, research, news, and seasonal evidence remain
  independent CommerceOS inputs.

## Evidence model

`IndustryGrowthProfile` identifies a reusable vertical. Immutable `IndustryGrowthEvidence` records
the source reference, observation, capture time, and confidence. `IndustryGrowthPattern` may record
customer problems, website, SEO, GEO, social, review, pricing, seasonality, buying, objection,
competitive, and service-outcome patterns only when it cites evidence owned by the same tenant and
industry profile.

No pattern is created from an unsupported model output. Missing information stays unknown.

## GEO boundary

GEO means Generative Engine Optimization: improving AI visibility and machine understanding. It is
not branded as AI SEO and is not a separate execution engine.

`GrowthGEOAssessment` is an advisory, evidence-backed view over website, social, and review signals.
It records visibility gaps and recommendations but cannot edit a website, social account, review,
listing, or external system.

## Growth services

`GrowthServiceRecommendation` connects prospect evidence to a suggested scope in website growth,
SEO, GEO, social growth, or review growth. Expected value must be framed without guarantees.
Purchase probability is optional and remains null when evidence is missing. Recommendations are
drafts without selling, contracting, discount, payment, or delivery authority.

Growth Gifts remain customer-specific trust builders rather than generic audits. Existing GrowthOS
approval and outreach rules continue to apply.

## Learning loop

`IndustryLearningSignal` captures sourced observations from conversations, objections, purchased
services, successful or failed offers, and manual review. It starts as a draft and may inform future
industry patterns, opportunity ranking, offers, and Sales Copilot only through governed review. It
does not rewrite source evidence.

## AI and security

- Reuse the governed AI Runtime and existing model-routing policies.
- Model selection remains configurable metadata, not a direct provider call introduced here.
- AI outputs remain analysis, classification, recommendation, or draft.
- Authentication, tenant scope, RBAC, evidence validation, audit logging, and human approval remain
  mandatory.
- No autonomous outreach, customer contact, negotiation, promises, discounting, contracting,
  payment collection, product creation, or other execution is authorized.
