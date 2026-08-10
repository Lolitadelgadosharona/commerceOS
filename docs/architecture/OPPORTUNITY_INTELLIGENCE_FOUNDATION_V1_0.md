# Opportunity Intelligence Foundation v1.0

Status: Sprint 004 implementation contract

## Purpose and ownership

Opportunity Intelligence records possible market openings, their evidence, product hypotheses, deterministic evaluation, and risks. Intelligence owns these observations. Decision continues to own `VentureOpportunity` and investment recommendations; Operations owns `SalesOpportunity`; Build owns products and Product Truth.

A qualified or highly scored `MarketOpportunity` has no execution, spending, approval, product-publication, or investment authority. Promotion into a venture workflow is a future explicit cross-domain command and is not implemented here.

## Model

- `MarketOpportunity` records organization, title, description, category, market, geography, trigger, timing window, status, and confidence.
- `OpportunityEvidence` records a supported future source type, source reference, supplied summary, and confidence. `customer_signal` references must be UUIDs belonging to the same organization. Other source types are references only; there are no retrieval connectors.
- `ProductCandidate` separates a product hypothesis and estimated margin from the underlying opportunity. It is not a Build-domain Product.
- `OpportunityScore` stores bounded input factors, calculated overall score, and formula version. One current versioned row exists per opportunity.
- `OpportunityRisk` records trademark, brand, policy, dispute, or payment risk with severity and status. Risk acceptance status does not represent Governance or owner approval.

## Deterministic scoring v1.0

All inputs are 0–100. Higher demand, pain, trend, and margin improve the score; higher competition, IP risk, and dispute risk reduce it.

```text
overall = demand × 0.25
        + pain × 0.15
        + trend × 0.15
        + margin × 0.20
        + (100 − competition) × 0.10
        + (100 − IP risk) × 0.075
        + (100 − dispute risk) × 0.075
```

The service rounds to two decimal places and stores formula version `v1.0`. Re-scoring updates the single versioned score row. Changing weights or factor semantics requires a new formula version and compatibility decision.

## API

The `/api/v1` resources are:

- `/opportunities`
- `/opportunity-evidence`
- `/product-candidates`
- `/opportunity-scores`
- `/opportunity-risks`

## Explicit exclusions

No Reddit, Amazon, Etsy, search, news, review, social, market-report, supplier, or Shopify connector exists. There is no scraping, LLM analysis, AI scoring, agent behavior, supplier matching, Investment Committee UI, or external data retrieval.

The Sprint 002 authentication activation limitation remains: these endpoints must not be publicly deployed until verified authentication and endpoint-wide authorization are implemented.
