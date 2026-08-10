# CFO and Revenue Intelligence Foundation v1.0

Status: Sprint 014 implementation contract

## Purpose and ownership

This foundation gives Commerce OS deterministic, tenant-scoped economic visibility without creating a ledger or an execution path for money movement. Finance owns financial periods, monetary observations, contribution-profit assessments, unit economics, and financial risk signals. Decision owns `CFOInsight` because its recommendation is advisory. Governance continues to own permissions and approvals.

## Financial periods and observations

`FinancialPeriod` provides organization-scoped daily, weekly, monthly, and quarterly reporting windows. Its lifecycle is `OPEN`, `CLOSED`, then `LOCKED`; a locked period is terminal.

`RevenueObservation` and `CostObservation` are append-only intelligence inputs. They preserve source and date context but are not accounting entries. Supported cost categories are product, shipping, advertising, platform fee, refund, dispute, operation, and creative cost. Observations never initiate payments, refunds, transfers, or journal entries.

Amounts are stored with an explicit ISO-style currency code. Assessments only aggregate observations in the requested currency; the system does not perform implicit exchange-rate conversion.

## Contribution profit

The frozen Sprint 014 calculation is:

```text
revenue
- product cost
- shipping cost
- acquisition (advertising) cost
- refund cost
- dispute cost
- operational cost
= contribution profit
```

Margin percentage is contribution profit divided by revenue. Platform and creative costs remain observable Finance facts but are excluded from this frozen contribution formula. Each assessment stores its component snapshot, confidence, product, period, and currency so the result is reproducible.

## Unit economics

`UnitEconomicAssessment` stores average order value, customer-acquisition cost, gross margin, refund rate, dispute rate, lifetime-value estimate, and a deterministic profitability score. The V1 score is:

```text
efficiency = clamp((lifetime value - acquisition cost) / max(lifetime value, 1), -1, 1)
net margin = gross margin - refund rate - dispute rate
score = clamp(50 + 25 * (net margin + efficiency), 0, 100)
```

The score is decision support, not a forecast guarantee or authority to change budgets or prices.

## CFO insights and financial risk

`CFOInsight` is a Decision-owned recommendation with type, severity, finding, impact, recommendation, confidence, and evidence scope. Supported initial types include profit decline, CAC increase, refund spike, and margin risk.

`FinancialRiskSignal` is a Finance-owned observation for loss, margin-compression, cash-flow, or high-refund risk. A signal must reference a financial period or product as evidence scope. Neither record can approve or execute a financial action.

## Tenant and authority boundaries

- Every record is scoped to an organization; project and product references must resolve inside that organization.
- Monetary observation endpoints are append-only.
- No API in this foundation issues payments, refunds, discounts, accounting entries, or other money movement.
- Recommendations do not become execution authority. Existing Finance and Governance approval contracts remain controlling.
- There are no Shopify, Stripe, banking, accounting, or other external finance connectors.
