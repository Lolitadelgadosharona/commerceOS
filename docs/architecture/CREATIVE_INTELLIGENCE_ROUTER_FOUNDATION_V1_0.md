# Creative Intelligence and Multi-Model Router Foundation v1.0

Status: frozen Sprint 013 implementation contract

## Purpose and ownership

Decision owns creative asset strategies, provider evaluations, routing recommendations, economic assessments, and reusable principle references. Existing Creative Strategy remains the upstream source of audience, objective, message, and creative direction. Build will own future generated artifacts. Growth will own future distribution. Governance owns approval. Finance owns actual cost, revenue, and contribution-profit truth.

Sprint 013 contains no provider adapter, credential, model identifier, network client, prompt execution, generation, artifact storage, publishing, advertising, or external integration.

## Creative asset strategy

An asset strategy links an organization-scoped Product and matching Creative Strategy to an audience, objective, recommended format, creative angle, confidence, and lifecycle. Formats are video, image, carousel, UGC, testimonial, educational, and comparison. The lifecycle is `draft -> recommended -> approved -> archived`, with archival exits. Approval records decision acceptance only; it cannot generate an asset.

## Provider registry

The provider registry is an internal evaluation catalogue for future image, video, voice, or editing capabilities. Provider names are labels, not integrations. Quality, cost efficiency, and speed are bounded 0–100 evaluation scores. Availability and lifecycle status allow the router to exclude unavailable, inactive, or deprecated candidates. No provider is contacted.

## Deterministic routing

Router version `creative-router-v1.0` considers only organization-scoped, active, available providers matching the required capability. It applies these weights:

| Factor | Weight |
|---|---:|
| Quality | 30% |
| Cost efficiency | 20% |
| Speed | 15% |
| Platform suitability | 20% |
| Historical performance | 15% |

Quality, cost, and speed come from the provider registry. Platform suitability and historical performance are optional supplied observations. Missing optional evidence remains null and the present weights are renormalized; history is never fabricated. The highest deterministic score wins, with stable provider-ID tie breaking. The decision stores the selected provider, factor snapshot, score, reason, confidence, and formula version. It is advisory and has no invocation path.

## Creative economics

Economic assessment version `creative-economics-v1.0` uses supplied planning estimates in a consistent value unit:

`risk_adjusted_value = expected_impact × confidence + test_value`

`profitability_score = clamp(50 + 50 × (risk_adjusted_value − estimated_production_cost) ÷ max(cost + impact + test_value, 1), 0, 100)`

This balances risk-adjusted impact, learning/test value, and cost rather than optimizing creative quality alone. These are Decision estimates—not expenses, revenue, budgets, payments, or contribution-profit ledger truth. Finance remains authoritative.

## Creative DNA pattern references

Pattern references store reusable internal principles for hooks, story structures, calls to action, and proof structures with source lineage and performance notes. They must describe principles rather than copy external creative assets. Performance notes are observations, not automatically measured truth.

## Authority and scope

Every record is organization-scoped and cross-tenant references/providers are rejected or excluded. Approved strategies and routing decisions do not authorize generation, publication, spend, or distribution. Existing authentication limitations continue to prohibit public deployment.

Explicitly excluded: image/video/voice generation, editing execution, LLMs, agents, OpenAI API, Nano Banana, TikTok, Meta, Pinterest, Google, publishing, and advertising execution.
