# Product Intelligence Foundation v1.0

Status: Sprint 005 implementation contract

## Purpose and ownership

Product Intelligence converts an Intelligence-owned `MarketOpportunity` into testable, economically evaluated product hypotheses. These records remain evidence and recommendations: they do not create a Build-domain `Product`, publish Product Truth, select a supplier, spend money, or authorize investment.

`ProductCandidate` remains the coarse opportunity-screening record introduced in Sprint 004. `ProductHypothesis` is the detailed solution hypothesis used for economics, supplier references, product-specific risk, and investment scoring. A future explicit Decision/Build workflow may promote an approved hypothesis; Sprint 005 does not.

## Model

- `ProductHypothesis` records the problem, proposed solution, target customer/market, lifecycle status, and confidence for one market opportunity.
- `ProductEconomics` stores one current versioned calculation per hypothesis. The API field `product_id` means the `ProductHypothesis` identifier.
- `SupplierCandidate` stores manually supplied references and estimates. It is not a Supplier source of truth, purchase authority, or connector result.
- `ProductRisk` records trademark, patent, brand, policy, dispute, or quality concerns. Accepting a risk record is not Governance approval.
- `ProductInvestmentScore` stores derived inputs, result, and formula version. It is advisory and has no approval or spending authority.

All records are organization-scoped. Child services verify the referenced opportunity or hypothesis belongs to the same organization.

## Economics v1.0

Money uses fixed-precision decimals and an uppercase three-letter currency code.

```text
contribution profit = selling price
                    - estimated product cost
                    - estimated shipping cost
                    - payment cost
                    - estimated marketing cost

margin percentage = contribution profit / selling price × 100
```

`contribution_margin` is the monetary contribution profit required by the Sprint 005 contract. Negative contribution profit is retained as decision evidence; input costs cannot be negative and selling price must be positive.

## Investment scoring v1.0

The service derives the opportunity input from its `OpportunityScore`, margin from `ProductEconomics`, risk from the highest open product risk (`low` 25, `medium` 50, `high` 75, `critical` 100; none 0), and confidence from the hypothesis. Competition is a bounded explicit input.

```text
overall = opportunity × 0.35
        + margin × 0.25
        + (100 − risk) × 0.15
        + (100 − competition) × 0.15
        + confidence × 0.10
```

Margin is clamped to 0–100 for scoring, the output is clamped to 0–100 and rounded to two decimals, and formula version `v1.0` is persisted. Missing opportunity scoring or economics prevents scoring.

## API and exclusions

The `/api/v1` resources are `/product-hypotheses`, `/product-economics`, `/supplier-candidates`, `/product-risks`, and `/product-investment-scores`.

There are no supplier APIs, supplier scraping, AliExpress, Alibaba, Shopify, listing generation, advertising, external integrations, LLMs, or agents. These endpoints remain internal and must not be publicly deployed until the documented authentication activation limitation is resolved.
