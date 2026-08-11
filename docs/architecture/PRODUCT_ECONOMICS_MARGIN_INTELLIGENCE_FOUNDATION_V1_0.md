# Product Economics and Margin Intelligence Foundation v1.0

Status: frozen for Sprint 024 implementation

## Purpose

This foundation estimates product profitability before commercial execution. It captures Intelligence-owned assumptions and produces advisory assessments. Estimates are not Finance ledger truth, payment instructions, budgets, purchase authority, or approvals.

## Ownership and authority

- Finance owns monetary truth and authoritative financial records.
- Intelligence owns `ProductEconomicProfile`, `ProductProfitAssessment`, `ProfitScenarioAssessment`, and `RiskAdjustedProfitAssessment` as assumptions and advisory estimates.
- Decision owns recommendations derived from assessments.
- Build owns Product Truth.
- Governance owns approvals.

All records carry `organization_id`; every write validates that the referenced `ProductCandidate` belongs to that organization. Sprint 024 never writes Finance observations, Governance approvals, or execution records.

## Decimal policy

Money uses fixed `NUMERIC(19,4)` storage and half-up rounding to four decimal places. Rates use `NUMERIC(7,6)`. Scores use `NUMERIC(7,4)`. Calculations remain decimal end to end; binary floating-point is not used for monetary formulas. Currency is a normalized three-letter uppercase code.

## Economic profile

The profile captures product, shipping, packaging, transaction, and estimated acquisition cost; refund and dispute rate assumptions; currency; and confidence. Profiles are append-only estimates so prior assessment provenance remains recoverable. The latest organization-scoped profile feeds new assessments.

## Profit formula v1

For a proposed selling price:

`gross margin = selling price - product cost - shipping - packaging - transaction cost`

`contribution profit = gross margin - acquisition cost - (selling price × refund rate) - (selling price × dispute rate)`

`margin score = clamp(contribution profit ÷ selling price × 100, 0, 100)`

The assessment inherits profile confidence and records formula version `product-profit-v1`. A negative contribution profit is retained while the bounded margin score becomes zero.

## Scenario model

Scenarios use the latest profile and profit assessment:

| Scenario | Revenue factor | Operating-cost factor | Refund/dispute-rate factor |
| --- | ---: | ---: | ---: |
| Conservative | 0.90 | 1.10 | 1.25 |
| Base | 1.00 | 1.00 | 1.00 |
| Optimistic | 1.05 | 0.95 | 0.75 |

Adjusted refund and dispute rates are capped at one. Each scenario stores revenue, total cost, profit, and unbounded signed margin percentage to preserve loss visibility.

## Risk-adjusted profit score

The latest product profit assessment supplies `profit_score`; the latest Sprint 023 product risk assessment supplies `risk_score`. The caller supplies a bounded opportunity score as advisory evidence.

`final score = opportunity × 35% + (100 - risk) × 35% + profit × 30%`

Recommendations are deterministic:

- `REJECT` when risk is at least 75 or final score is below 40.
- `GO` when final score is at least 70 and risk is below 40.
- `TEST` when final score is at least 55 and risk is below 60.
- `REVIEW` otherwise.

These labels do not approve a product or initiate commercial activity.

## API boundary

- `/api/v1/product-economic-profiles`
- `/api/v1/product-profit-assessments`
- `/api/v1/profit-scenarios`
- `/api/v1/risk-adjusted-profit-assessments`

The API exposes assumption capture, deterministic simulation, and organization-scoped reads. It exposes no payment, purchasing, approval, publishing, or execution route.

## Explicit exclusions

No payments, Shopify, ads, supplier purchasing, LLM, agent, automation, Finance ledger mutation, Product Truth mutation, or approval creation is included.
