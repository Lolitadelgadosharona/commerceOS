# Commerce OS Finance Authority Model v1.0

Status: v1 human-authority control baseline

## Governing rule

AI may calculate, reconcile, forecast, draft, recommend, request approval, and execute an already approved action within its exact scope. AI may not create its own authority. Deterministic policy and authenticated human approval override model output. Any ambiguity, amount mismatch, expired approval, changed recipient/terms, or policy failure stops execution and requests review.

“Owner” below means an authenticated human with recorded authority for the legal entity, account, action type, and amount—not merely a user with a dashboard session.

## Authority matrix

| Action | AI executable without new owner approval | Owner approval required | Required evidence/control |
|---|---|---|---|
| Refund | Validate eligibility, calculate amount, draft response, request approval | Every monetary refund in v1; changed amount/recipient requires reapproval | Order/payment match, reason, amount/currency, approver authority, idempotency, provider receipt |
| Discount | Apply a pre-approved published promotion with zero discretionary exception and no new commitment | Custom, discretionary, stacked, margin-floor-breaching, or policy-exception discount | Policy/version, eligible SKU/customer/window, margin impact, before/after price |
| Advertising budget | Analyze, recommend, simulate, pause on safety/policy trigger if pre-authorized and non-spending | Every paid launch, budget increase/decrease/reallocation, new campaign commitment, or restart in v1 | Channel/account, amount/period/cap, forecast/risk, approval scope/expiry, execution receipt |
| Supplier payment | Reconcile invoice and PO, detect anomaly, draft payment batch | Every payment/release; any bank-detail or payee change requires independent verification and approval | Supplier verification, invoice/PO/receipt, bank token, duplicate check, segregation of duties |
| Custom commitment | Draft terms, compare policy, flag risk, request approval | Any bespoke delivery, SLA, warranty, indemnity, exclusivity, volume, legal, or incremental-cost promise | Counterparty, exact terms, cost/risk, legal/operations review where applicable, expiry |
| Pricing exception | Recommend and simulate | Any price outside approved catalog/promotion or below margin/floor policy | Product/customer, list and proposed price, quantity/term, margin/cash impact, approver |

## AI-executable financial-support actions

Within read permissions, AI may classify/reconcile records, calculate unit economics and variance, detect duplicates/anomalies, produce forecasts with assumptions, prepare approval packets, and monitor approved caps. Within an explicit versioned policy it may execute zero-incremental-cost administrative actions such as tagging, routing, scheduling internal review, and sending non-committal status messages.

Execution of an approved monetary action requires an approval bound to action type, legal entity/account, counterparty, amount/currency or hard cap, purpose, time window, relevant before/after values, policy version, approver, and idempotency key. Partial execution and retries reconcile against receipts and may never exceed the cap.

## Control and audit requirements

- Finance owns transaction, expense, and revenue truth and financial-control definitions.
- Governance owns the approval record and validates authority; the executing domain owns execution state.
- Requester, approver, executor, and reconciler are separated according to risk; AI is never the approver.
- Approvals expire and are invalidated by material input changes.
- Corrections use compensating entries/events; audit history is not overwritten.
- Emergency stops may prevent further loss but cannot initiate spend or conceal activity.

See the [Constitution](./AI_COMMERCE_OS_CONSTITUTION_V1_0.md) and [Data Ownership Contract](./DATA_OWNERSHIP_CONTRACT_V1_0.md).
